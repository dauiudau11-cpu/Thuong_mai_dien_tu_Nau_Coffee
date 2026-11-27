# Additive migration. NEVER apply to dev/production without a verified backup and owner approval.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('commerce', '0003_orderitem_recipe_snapshot')]

    operations = [
        migrations.AddField(
            model_name='order', name='bill_issued_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order', name='delivery_deadline_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order', name='delivered_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='order', name='status',
            field=models.CharField(max_length=30, choices=[
                ('PENDING_PAYMENT', 'Chờ thanh toán mô phỏng'),
                ('PENDING_CONFIRMATION', 'Chờ nhân viên xác nhận'),
                ('CONFIRMED', 'Đã xác nhận'),
                ('PREPARING', 'Đang pha chế'),
                ('READY', 'Đã sẵn sàng'),
                ('PICKUP_WAITING', 'Chờ khách nhận'),
                ('DELIVERING', 'Đang giao mô phỏng'),
                ('COMPLETED', 'Hoàn tất'),
                ('CANCELLED', 'Đã hủy'),
                ('DELIVERY_FAILED', 'Giao thất bại'),
            ]),
        ),
        migrations.AlterField(
            model_name='payment', name='method',
            field=models.CharField(max_length=20, choices=[
                ('COD', 'COD mô phỏng'),
                ('PAY_AT_PICKUP', 'Thanh toán khi nhận (demo)'),
                ('MOCK_ONLINE', 'Thanh toán online mô phỏng'),
                ('EXTERNAL_DEMO', 'Đối soát bên ngoài mô phỏng'),
                ('BANK_TRANSFER_DEMO', 'Chuyển khoản mô phỏng'),
            ]),
        ),
    ]
