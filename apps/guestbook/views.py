from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext as _
from django.core.paginator import Paginator
from .models import GuestbookEntry
from .forms import GuestbookForm

class GuestbookView(CreateView):
    model = GuestbookEntry
    form_class = GuestbookForm
    template_name = "guestbook/index.html"
    success_url = reverse_lazy("guestbook:index")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 优化查询：按时间倒序
        queryset = GuestbookEntry.objects.filter(is_public=True).select_related('user').order_by('-created_at')
        
        # 分页逻辑
        paginator = Paginator(queryset, 18)  # 每页 18 条 (3列布局刚好6行)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context["entries"] = page_obj
        context["page_obj"] = page_obj
        context["is_paginated"] = page_obj.has_other_pages()
        context["paginator"] = paginator
        return context

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.user = self.request.user
            form.instance.nickname = self.request.user.nickname or self.request.user.username
            form.instance.email = self.request.user.email
        
        messages.success(self.request, _("留言发布成功！"))
        return super().form_valid(form)
