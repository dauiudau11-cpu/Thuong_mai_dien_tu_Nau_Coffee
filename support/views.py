from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from commerce.models import Order
from catalog.models import Product
from .forms import MessageForm, ReviewForm
from .models import Policy
from .services import allow_submission, submit_review


def contact(request, kind='CONTACT'):
    initial = {}
    if request.method != 'POST' and request.user.is_authenticated:
        profile = getattr(request.user, 'customer_profile', None)
        initial = {'name': profile.full_name if profile else request.user.get_full_name(),
                   'email': profile.email if profile else request.user.email}
    form = MessageForm(request.POST if request.method == 'POST' else None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        order = None
        if form.cleaned_data['website'] or not allow_submission(request, 'support'):
            form.add_error(None, 'Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau 10 phút.')
        elif form.cleaned_data['order_code'] and (not request.user.is_authenticated or not (
                order := Order.objects.filter(user=request.user, public_code=form.cleaned_data['order_code']).first())):
            form.add_error('order_code', 'Không tìm thấy đơn của bạn. Hãy đăng nhập bằng tài khoản đặt đơn.')
        else:
            entry = form.save(commit=False)
            entry.kind, entry.order = kind, order
            entry.user = request.user if request.user.is_authenticated else None
            entry.save()
            messages.success(request, 'Nâu đã nhận được lời nhắn của bạn. Cảm ơn bạn đã liên hệ với Nâu Coffee!')
            return redirect('contact' if kind == 'CONTACT' else 'feedback')
    return render(request, 'support/contact.html', {'form': form, 'is_feedback': kind == 'FEEDBACK'})


POLICIES = {
    'returns': ('Đổi trả & hủy đơn', 'Bạn có thể hủy trước khi pha chế tại trang đơn hàng. Nếu cần thay đổi món, hãy hủy và đặt lại. Với món sai hoặc nghi ngờ chất lượng, gửi phản hồi kèm mã đơn; nhân viên sẽ xác minh trước khi đề xuất đổi hoặc hoàn mô phỏng. Không tự động hoàn tiền.'),
    'warranty': ('Đảm bảo chất lượng', 'Đồ uống là sản phẩm dễ hỏng, không áp dụng bảo hành kỹ thuật dài hạn. Khi nhận món không đúng hoặc có vấn đề chất lượng, vui lòng ngừng sử dụng và liên hệ để được tiếp nhận, xác minh.'),
    'shipping': ('Nhận món & vận chuyển', 'Website chỉ nhận đơn đặt trước và nhận tại quán; phí giao bằng 0. Thanh toán trực tuyến mô phỏng. Hệ thống tự chọn lịch sớm nhất còn chỗ theo giờ phục vụ và thời gian chuẩn bị. Muốn giao tận nơi, truy cập trang đối tác; chưa xác nhận gian hàng Nâu Coffee trên các nền tảng. Địa chỉ liên hệ: 457/9 Điện Biên Phủ, phường Bàn Cờ, TP.HCM.'),
    'privacy': ('Quyền riêng tư', 'Tên, email, số điện thoại và địa chỉ được dùng cho luồng đơn hàng/hỗ trợ; không đăng công khai. Không nhập dữ liệu thẻ hay mật khẩu vào nội dung phản hồi. Liên hệ quản trị để yêu cầu xử lý dữ liệu thử nghiệm.'),
    'terms': ('Điều khoản sử dụng', 'Điều kiện giao dịch hiện hành được trình bày tại đây; bản cập nhật cần được duyệt trước khi công bố. Website chỉ nhận đặt trước và nhận tại quán; thanh toán trực tuyến mô phỏng, không thu tiền thật. Các liên kết giao món dẫn tới nền tảng bên ngoài, chưa xác nhận gian hàng hoặc tích hợp vận chuyển.'),
    'loyalty': ('Điểm thành viên', 'Mặc định 1 điểm cho mỗi 10.000đ giá trị món sau khuyến mãi, không gồm phí giao. Chỉ cộng cho đơn hoàn tất đã ghi nhận thanh toán mô phỏng. Điểm không có giá trị quy đổi tiền; mọi thay đổi được lưu lịch sử.'),
}


def policy(request, slug):
    from . import policies
    if policies.enabled():
        canonical = {'warranty':'returns'}.get(slug,slug)
        revision=policies.active().get(canonical)
        if revision is not None:
            return render(request,'support/policy.html',{'title':revision.title,'body':revision.body,'revision':revision})
        if slug!='loyalty':raise Http404
    if slug not in POLICIES:
        raise Http404
    title, body = POLICIES[slug]
    saved = Policy.objects.filter(slug=slug).first()
    if saved and slug not in ('shipping', 'terms'):
        title, body = saved.title, saved.body
    return render(request, 'support/policy.html', {'title': title, 'body': body})


@login_required
@require_POST
def review(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True, category__is_active=True)
    form = ReviewForm(request.POST)
    if not allow_submission(request, 'review'):
        messages.error(request, 'Vui lòng thử lại sau 10 phút.')
    elif form.is_valid():
        try:
            submit_review(request.user, product, form.cleaned_data)
            messages.success(request, 'Đánh giá đã được gửi và đang chờ kiểm duyệt.')
        except ValidationError as error:
            messages.error(request, ' '.join(error.messages))
    else:
        messages.error(request, 'Điểm đánh giá phải từ 1–5 và nội dung từ 5–2000 ký tự.')
    return redirect('product', slug=slug)
