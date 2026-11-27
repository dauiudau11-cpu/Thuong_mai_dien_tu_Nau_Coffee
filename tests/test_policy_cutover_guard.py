from unittest import TestCase
from unittest.mock import patch
from scripts.policy_cutover import require,docker_sql
class PolicyCutoverGuardTests(TestCase):
    def test_preview_writes_and_unknown_databases_rejected_before_process(self):
        with patch('scripts.policy_cutover.run') as run:
            for container,db,readonly in [('pg_lab_postgres','nau_coffee_dev',True),('pg_lab_postgres','nau_coffee_test',False),('nau_localization_qa_20261111','unexpected',True),('unknown','postgres',True)]:
                with self.assertRaises(RuntimeError):docker_sql(container,db,'SELECT 1;',readonly)
            run.assert_not_called()
    def test_guard_does_not_depend_on_python_assertions(self):
        with self.assertRaises(RuntimeError):require(False,'Denied')

    def test_restore_constraint_normalization_is_narrow_and_never_accepts_new_values(self):
        from scripts.policy_cutover import canonical_constraint
        source="CHECK (((audience)::text = ANY ((ARRAY['PUBLIC'::character varying, 'PRIVATE'::character varying])::text[])))"
        restored="CHECK (((audience)::text = ANY (ARRAY[('PUBLIC'::character varying)::text, ('PRIVATE'::character varying)::text])))"
        self.assertEqual(canonical_constraint('commerce_vouchercampaign','voucher_v2_audience',source),canonical_constraint('commerce_vouchercampaign','voucher_v2_audience',restored))
        with self.assertRaises(RuntimeError):canonical_constraint('commerce_vouchercampaign','voucher_v2_audience',source.replace("'PRIVATE'","'APP'"))
