from django.views.generic import DetailView, View, ListView
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
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
        return Poll.objects.filter(is_active=True).order_by("-created_at")


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
            context["has_voted"] = Vote.objects.filter(
                poll=self.object, user=user
            ).exists()
        else:
            context["has_voted"] = False
        return context


class PollVoteView(LoginRequiredMixin, View):
    """
    投票动作视图 (AJAX)。

    处理用户的投票请求，采用原子事务保证数据一致性。

    处理逻辑：
    1. 验证 Poll 和 Choice 是否存在。
    2. 检查用户是否已投票（支持区分单选/多选逻辑）。
    3. 创建 Vote 记录。
    4. 原子更新 Choice 的票数。
    5. 返回更新后的投票结果 (HTMX 片段)。
    """

    def post(self, request, pk):
        from django.db import transaction

        poll = get_object_or_404(Poll, pk=pk)

        # 获取用户提交的选项 ID (可能是单个值或列表)
        if poll.allow_multiple_choices:
            choice_ids = request.POST.getlist("choice")
        else:
            choice_id = request.POST.get("choice")
            choice_ids = [choice_id] if choice_id else []

        if not choice_ids:
            return HttpResponse(
                f'<div class="alert alert-warning">{_("请至少选择一个选项！")}</div>'
            )

        # 验证所有选项是否属于该投票
        choices = list(Choice.objects.filter(pk__in=choice_ids, poll=poll))
        if len(choices) != len(choice_ids):
             return HttpResponse(
                f'<div class="alert alert-error">{_("包含无效的选项！")}</div>'
            )

        # 检查是否允许投票
        # 1. 如果不允许重复投票 (单选)，检查用户是否已参与过该投票。
        # 2. 如果允许重复投票 (多选)，检查用户是否已投过该特定选项 (防止重复刷票)。

        has_voted_poll = Vote.objects.filter(poll=poll, user=request.user).exists()
        
        # 渲染结果页面的辅助函数
        def render_result():
            context = {"poll": poll, "has_voted": True}
            return render(request, "voting/partials/poll_results.html", context)

        if not poll.allow_multiple_choices:
            # 单选模式：如果已投过票，禁止再次投票
            if has_voted_poll:
                return render_result()
        else:
            # 多选模式：检查提交的选项中是否有已经投过的
            existing_votes = Vote.objects.filter(
                poll=poll, user=request.user, choice__in=choices
            ).exists()
            if existing_votes:
                 # 如果试图投已经投过的选项，返回错误或结果
                 # 这里简单起见直接返回结果，意味着不能重复投同一个选项
                 return render_result()

        try:
            with transaction.atomic():
                # 二次检查防止并发
                if not poll.allow_multiple_choices:
                    if Vote.objects.filter(poll=poll, user=request.user).exists():
                        raise ValueError("Already voted for this poll")
                else:
                    if Vote.objects.filter(poll=poll, user=request.user, choice__in=choices).exists():
                        raise ValueError("Already voted for one of these choices")

                # 批量创建投票记录
                votes_to_create = [
                    Vote(poll=poll, user=request.user, choice=choice)
                    for choice in choices
                ]
                Vote.objects.bulk_create(votes_to_create)

                # 增加票数 (原子更新)
                # F 对象不支持在 update 中引用自身进行批量更新不同值，所以需要循环
                # 或者使用 Case/When，但对于少量选项，循环更新可接受
                for choice in choices:
                    Choice.objects.filter(pk=choice.pk).update(votes_count=F("votes_count") + 1)

        except ValueError:
            return render_result()

        return render_result()
