from django.db import migrations

SQL = '''
CREATE FUNCTION nau_policy_revision_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Policy history cannot be deleted'; END IF;
 IF TG_OP='UPDATE' AND OLD.published_at IS NOT NULL AND
   (to_jsonb(NEW)-'status') IS DISTINCT FROM (to_jsonb(OLD)-'status') THEN
   RAISE EXCEPTION 'Published policy content is immutable';
 END IF;
 IF NEW.status='PUBLISHED' AND (NOT NEW.reviewed OR NEW.published_at IS NULL OR NEW.effective_at IS NULL OR trim(NEW.review_note)='') THEN
   RAISE EXCEPTION 'Publication requires approval and effective date';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER nau_policy_revision_guard BEFORE UPDATE OR DELETE OR INSERT ON support_policyrevision FOR EACH ROW EXECUTE FUNCTION nau_policy_revision_guard();
CREATE FUNCTION nau_consent_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Consent evidence is append only'; END $$;
CREATE TRIGGER nau_consent_append_only BEFORE UPDATE OR DELETE ON support_consentevent FOR EACH ROW EXECUTE FUNCTION nau_consent_append_only();
CREATE FUNCTION nau_policy_slug_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.slug IS DISTINCT FROM OLD.slug AND EXISTS(SELECT 1 FROM support_policyrevision WHERE policy_id=OLD.id AND published_at IS NOT NULL) THEN
  RAISE EXCEPTION 'Published policy URL is immutable';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER nau_policy_slug_guard BEFORE UPDATE ON support_policy FOR EACH ROW EXECUTE FUNCTION nau_policy_slug_guard();
'''
REVERSE='''
DROP TRIGGER nau_policy_slug_guard ON support_policy;
DROP FUNCTION nau_policy_slug_guard();
DROP TRIGGER nau_consent_append_only ON support_consentevent;
DROP FUNCTION nau_consent_append_only();
DROP TRIGGER nau_policy_revision_guard ON support_policyrevision;
DROP FUNCTION nau_policy_revision_guard();
'''

def install(apps,schema_editor):
    if schema_editor.connection.vendor=='postgresql':schema_editor.execute(SQL)
def remove(apps,schema_editor):
    if schema_editor.connection.vendor=='postgresql':schema_editor.execute(REVERSE)

class Migration(migrations.Migration):
    dependencies=[('support','0003_policyrevision_consentevent')]
    operations=[migrations.RunPython(install,remove)]
