from django.views.generic import DetailView, View, ListView
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext as _
from django.db.models import F
from .models import Poll, Choice, Vote

class PollListView(ListView):
    """
    投票列表视图

    展示所有开启的投票活动。
    """
    model = Poll
    template_name = "voting/poll_list.html"
    context_object_name = "polls"
    paginate_by = 12
    
    def get_queryset(self):
        return Poll.objects.filter(is_active=True).order_by('-created_at')

class PollDetailView(DetailView):
    """
    投票详情视图

    展示投票的详细信息和选项。
    如果用户已登录，会检查用户是否已经投票。
    """
    model = Poll
    template_name = "voting/poll_detail.html"
    context_object_name = "poll"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            context["has_voted"] = Vote.objects.filter(poll=self.object, user=user).exists()
        else:
            context["has_voted"] = False
        return context

class PollVoteView(LoginRequiredMixin, View):
    """
    投票动作视图 (AJAX)

    处理用户的投票请求。
    
    逻辑：
    1. 检查是否重复投票。
    2. 验证选项有效性。
    3. 创建 Vote 记录。
    4. 原子更新 Choice 的票数。
    5. 返回更新后的投票结果 (HTMX 片段)。
    """
    def post(self, request, pk):
        from django.db import transaction
        
        poll = get_object_or_404(Poll, pk=pk)
        
        choice_id = request.POST.get("choice")
        if not choice_id:
            return HttpResponse(f'<div class="alert alert-warning">{_("请选择一个选项！")}</div>')
            
        choice = get_object_or_404(Choice, pk=choice_id, poll=poll)

        # 检查是否允许投票 (Check if voting is allowed)
        # 1. 如果不允许重复投票，检查是否已投过该 Poll
        # 2. 如果允许重复投票 (多选)，检查是否已投过该选项
        
        has_voted_poll = Vote.objects.filter(poll=poll, user=request.user).exists()
        has_voted_choice = Vote.objects.filter(poll=poll, user=request.user, choice=choice).exists()

        if poll.allow_multiple_choices:
             if has_voted_choice:
                # 已经投过这个选项了
                context = {"poll": poll, "has_voted": True}
                return render(request, "voting/partials/poll_results.html", context)
        else:
             if has_voted_poll:
                # 已经投过票了 (单选)
                context = {"poll": poll, "has_voted": True}
                return render(request, "voting/partials/poll_results.html", context)

        try:
            with transaction.atomic():
                #再一次检查防止并发 (Double check for concurrency)
                if poll.allow_multiple_choices:
                    if Vote.objects.filter(poll=poll, user=request.user, choice=choice).exists():
                         raise ValueError("Already voted for this choice")
                else:
                    if Vote.objects.filter(poll=poll, user=request.user).exists():
                         raise ValueError("Already voted for this poll")

                # 创建投票记录 (Create Vote)
                Vote.objects.create(poll=poll, user=request.user, choice=choice)
                
                # 增加票数 (Increment Count - Atomic)
                Choice.objects.filter(pk=choice_id).update(votes_count=F("votes_count") + 1)
        except ValueError:
            # 并发导致重复投票，直接返回结果
            context = {"poll": poll, "has_voted": True}
            return render(request, "voting/partials/poll_results.html", context)
            
        # 返回更新后的结果 (Return updated poll results - HTMX)
        context = {
            "poll": poll,
            "has_voted": True
        }
        return render(request, "voting/partials/poll_results.html", context)
