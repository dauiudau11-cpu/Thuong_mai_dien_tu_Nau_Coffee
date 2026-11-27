"""Vietnamese presentation vocabulary. Database keys and model metadata stay intact."""
MODEL_NAMES = {
    'catalog': ('Thực đơn', {'category':'Danh mục','product':'Sản phẩm','productvariant':'Biến thể SKU',
        'channelprice':'Giá theo kênh','productimage':'Ảnh sản phẩm','productoption':'Tùy chọn sản phẩm',
        'standardcost':'Chi phí nguyên liệu chuẩn','address':'Địa chỉ'}),
    'commerce': ('Bán hàng và vận hành', {'cart':'Giỏ hàng','cartitem':'Món trong giỏ','order':'Đơn hàng',
        'orderitem':'Món trong đơn','payment':'Thanh toán','paymentevent':'Lịch sử thanh toán',
        'orderstatushistory':'Lịch sử trạng thái đơn','voucher':'Mã giảm giá','voucherredemption':'Lượt dùng mã giảm giá',
        'storesettings':'Cấu hình cửa hàng','ingredient':'Nguyên liệu','recipeline':'Định mức nguyên liệu',
        'optionrecipeline':'Định mức tùy chọn','stockmovement':'Biến động kho','loyaltyledger':'Lịch sử điểm thành viên'}),
    'support': ('Chăm sóc khách hàng', {'policy':'Chính sách','message':'Liên hệ và phản hồi','review':'Đánh giá'}),
    'auth': ('Tài khoản và phân quyền', {'user':'Người dùng','group':'Nhóm quyền','permission':'Quyền truy cập'}),
}
FIELD_LABELS = {
    'image':'Ảnh sản phẩm','id':'ID','code':'Mã','kind':'Loại','amount':'Giá trị','cap':'Mức giảm tối đa',
    'min_subtotal':'Giá trị đơn tối thiểu','max_uses':'Tổng lượt dùng tối đa','per_user_limit':'Lượt dùng tối đa mỗi người',
    'starts_at':'Bắt đầu lúc','ends_at':'Kết thúc lúc','is_active':'Đang hoạt động',
    'allow_sale_stacking':'Cho phép cộng dồn với giá khuyến mãi','created_at':'Ngày tạo','updated_at':'Ngày cập nhật',
    'name':'Tên','slug':'Đường dẫn tĩnh','description':'Mô tả','category':'Danh mục','product':'Sản phẩm',
    'is_featured':'Sản phẩm nổi bật','sku':'Mã SKU','size':'Cỡ ly','volume_ml':'Dung tích (ml)',
    'is_available':'Còn phục vụ','price_delta':'Giá cộng thêm','variant':'Biến thể SKU','channel':'Kênh bán',
    'original_price':'Giá gốc','sale_price':'Giá khuyến mãi','sale_starts_at':'Bắt đầu khuyến mãi',
    'sale_ends_at':'Kết thúc khuyến mãi','url':'Đường dẫn ảnh','alt':'Mô tả ảnh','sort_order':'Thứ tự hiển thị',
    'ingredient_cost':'Chi phí nguyên liệu','user':'Người dùng','session_key':'Mã phiên',
    'cart':'Giỏ hàng','quantity':'Số lượng','options':'Tùy chọn','config_key':'Mã cấu hình',
    'public_code':'Mã đơn hàng','placed_by':'Người tạo đơn','fulfillment':'Phương thức nhận',
    'customer_name':'Tên khách hàng','phone':'Số điện thoại','address':'Địa chỉ','notes':'Ghi chú',
    'scheduled_for':'Giờ nhận dự kiến','delivery_verified':'Đã xác minh giao hàng',
    'delivery_distance_km':'Khoảng cách giao (km)','bill_issued_at':'Thời điểm xuất phiếu',
    'delivery_deadline_at':'Hạn giao hàng','delivered_at':'Thời điểm giao hàng',
    'external_reference':'Mã tham chiếu ngoài','subtotal':'Tạm tính','discount':'Giảm giá',
    'shipping':'Phí giao hàng','total':'Tổng tiền','status':'Trạng thái','idempotency_key':'Mã chống xử lý trùng',
    'order':'Đơn hàng','product_name':'Tên món đã đặt','options_snapshot':'Tùy chọn tại thời điểm đặt',
    'recipe_snapshot':'Công thức tại thời điểm đặt','unit_price':'Đơn giá','line_total':'Thành tiền',
    'token':'Mã giao dịch','method':'Phương thức thanh toán','paid_at':'Thời điểm thanh toán',
    'refunded_at':'Thời điểm hoàn tiền','payment':'Thanh toán','event_key':'Sự kiện thanh toán',
    'actor':'Người thực hiện','from_state':'Trạng thái trước','to_state':'Trạng thái sau','reason':'Lý do',
    'voucher':'Mã giảm giá','delivery_fee':'Phí giao hàng','free_delivery_min':'Đơn tối thiểu miễn phí giao',
    'opens_at':'Giờ mở cửa','closes_at':'Giờ đóng cửa','lead_minutes':'Thời gian chuẩn bị (phút)',
    'preorder_days':'Số ngày được đặt trước','slot_capacity':'Số đơn tối đa mỗi khung giờ',
    'loyalty_vnd_per_point':'Số đồng cho mỗi điểm','unit':'Đơn vị','low_stock_threshold':'Ngưỡng cảnh báo tồn kho',
    'ingredient':'Nguyên liệu','option':'Tùy chọn','delta':'Biến động','note':'Ghi chú','event':'Sự kiện',
    'email':'Thư điện tử','subject':'Chủ đề','body':'Nội dung','admin_reply':'Phản hồi của quản trị viên',
    'item':'Món trong đơn','rating':'Điểm đánh giá','moderated_by':'Người duyệt','title':'Tiêu đề',
    'label':'Tên gợi nhớ','recipient':'Người nhận','text':'Địa chỉ',
}
DISPLAY_VALUES = {
    'WEB':'Website','COUNTER':'Tại quầy','APP':'Ứng dụng giao món (APP)',
    'GUEST':'Khách vãng lai','CUSTOMER':'Khách hàng','STAFF':'Nhân viên','ADMIN':'Quản trị viên',
    'PENDING_PAYMENT':'Chờ thanh toán','PENDING_CONFIRMATION':'Chờ xác nhận','CONFIRMED':'Đã xác nhận',
    'PREPARING':'Đang pha chế','READY':'Sẵn sàng nhận','PICKUP_WAITING':'Chờ khách nhận',
    'DELIVERING':'Đang giao hàng','COMPLETED':'Hoàn tất','CANCELLED':'Đã hủy','DELIVERY_FAILED':'Giao thất bại',
    'UNPAID':'Chưa thanh toán','PENDING':'Đang chờ','PAID':'Đã thanh toán mô phỏng',
    'FAILED':'Thanh toán mô phỏng thất bại','REFUND_PENDING':'Chờ hoàn tiền mô phỏng','REFUNDED':'Đã hoàn tiền mô phỏng',
    'MOCK_ONLINE':'Thanh toán trực tuyến mô phỏng','COD':'Thanh toán khi giao mô phỏng',
    'PAY_AT_PICKUP':'Thanh toán khi nhận mô phỏng','EXTERNAL_DEMO':'Đối soát bên ngoài mô phỏng',
    'BANK_TRANSFER_DEMO':'Chuyển khoản mô phỏng','PICKUP':'Nhận tại quán','DELIVERY':'Giao hàng',
    'TOPPING':'Phần thêm','FIXED':'Cố định','STANDARD':'Tiêu chuẩn','NEW':'Mới','WORKING':'Đang xử lý',
    'RESOLVED':'Đã xử lý','APPROVED':'Đã duyệt','REJECTED':'Từ chối','piece':'cái',
    'mock_success':'Thanh toán mô phỏng thành công','mock_failure':'Thanh toán mô phỏng thất bại',
    'cash_demo':'Ghi nhận tiền mặt mô phỏng','bank_transfer_demo':'Xác nhận chuyển khoản mô phỏng',
    'mock_refund':'Xác nhận hoàn tiền mô phỏng','external_demo':'Đối soát bên ngoài mô phỏng',
    'payment_success':'Thanh toán mô phỏng thành công','payment_failed':'Thanh toán mô phỏng thất bại',
    'refund_requested':'Yêu cầu hoàn tiền mô phỏng','refund_success':'Hoàn tiền mô phỏng thành công',
}


def model_name(model):
    opts = model._meta
    return MODEL_NAMES.get(opts.app_label, ('', {}))[1].get(opts.model_name, str(opts.verbose_name))


def display_value(value):
    if value is None or value == '':
        return '—'
    return DISPLAY_VALUES.get(str(value), value)


def object_label(obj):
    from django.db.models import Model
    if obj._meta.label_lower == 'auth.group':
        return display_value(obj.name)
    if obj._meta.label_lower == 'auth.permission':
        action = {'add':'Thêm','change':'Sửa','delete':'Xóa','view':'Xem'}.get(obj.codename.split('_', 1)[0])
        names = MODEL_NAMES.get(obj.content_type.app_label, ('', {}))[1]
        if action and obj.content_type.model in names:
            return f'{action} {names[obj.content_type.model].lower()}'
    if obj.__class__.__str__ is Model.__str__:
        return f'{model_name(obj)} #{obj.pk}'
    return str(obj)

# Policy audit labels affect Admin presentation only, not field/database names.
FIELD_LABELS.update({'purpose':'Mục đích / xác nhận','state':'Trạng thái','source':'Nguồn thao tác',
    'revision':'Phiên bản chính sách','operation_id':'Mã thao tác','content_hash':'Hash nội dung',
    'method':'Cách thể hiện','effective_at':'Ngày hiệu lực','reviewed':'Đã duyệt nội dung',
    'review_note':'Ghi chú duyệt','published_at':'Thời điểm công bố','substantial_change':'Thay đổi đáng kể'})
