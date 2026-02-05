from typing import Any, Dict
from django.utils import timezone
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils.translation import gettext as _
from datetime import timedelta
import psutil
import platform
import django
import json

from blog.models import Post, Comment, Category, Tag
from users.models import User

class DashboardService:
    """
    Service for gathering dashboard statistics and charts data.
    """

    @staticmethod
    def get_dashboard_context() -> Dict[str, Any]:
        context = {}
        context["dashboard_title"] = _("Rosetta Dashboard")

        # 1. 关键指标统计 (Key Metrics)
        today = timezone.now()
        last_month = today - timedelta(days=30)
        trend_start_date = today - timedelta(days=7)

        post_counts = Post.objects.aggregate(
            total=Count("id"),
            last_month=Count("id", filter=Q(created_at__gte=last_month)),
        )
        total_posts = post_counts["total"] or 0
        posts_last_month = post_counts["last_month"] or 0

        # 计算增长率
        total_prev = total_posts - posts_last_month
        post_growth = 0
        if total_prev > 0:
            post_growth = (posts_last_month / total_prev) * 100
        elif posts_last_month > 0:
            post_growth = 100

        context["total_posts"] = total_posts
        context["post_growth"] = round(post_growth, 1)

        # 评论数据
        comment_counts = Comment.objects.aggregate(
            total=Count("id"),
            pending=Count("id", filter=Q(active=False)),
            active=Count("id", filter=Q(active=True)),
        )
        total_comments = comment_counts["total"] or 0
        pending_comments = comment_counts["pending"] or 0
        active_comments = comment_counts["active"] or 0
        
        context["total_comments"] = total_comments
        context["pending_comments"] = pending_comments

        # 2. 图表数据
        context["comment_status_data"] = json.dumps([active_comments, pending_comments])

        # 用户角色分布
        user_counts = User.objects.aggregate(
            superusers=Count("id", filter=Q(is_superuser=True)),
            staff=Count("id", filter=Q(is_staff=True, is_superuser=False)),
            normal=Count("id", filter=Q(is_staff=False)),
        )
        context["user_role_data"] = [
            user_counts["superusers"] or 0,
            user_counts["staff"] or 0,
            user_counts["normal"] or 0,
        ]

        # 评论趋势
        trend_data = (
            Comment.objects.filter(created_at__gte=trend_start_date)
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )
        
        # 用户注册趋势
        user_trend = (
            User.objects.filter(date_joined__gte=trend_start_date)
            .annotate(date=TruncDate("date_joined"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        date_map = {item["date"]: item["count"] for item in trend_data}
        user_date_map = {item["date"]: item["count"] for item in user_trend}
        
        dates = []
        counts = []
        user_counts_list = []
        
        for i in range(7):
            d = (trend_start_date + timedelta(days=i)).date()
            dates.append(d.strftime("%m-%d"))
            counts.append(date_map.get(d, 0))
            user_counts_list.append(user_date_map.get(d, 0))

        context["trend_dates"] = json.dumps(dates, ensure_ascii=False)
        context["trend_counts"] = json.dumps(counts)
        context["user_trend_counts"] = json.dumps(user_counts_list)

        # 热门文章
        top_posts = list(Post.objects.only("id", "title", "views").order_by("-views")[:5])
        context["top_posts"] = top_posts
        context["top_posts_labels"] = [
            p.title[:10] + "..." if len(p.title) > 10 else p.title for p in top_posts
        ]

        # 分类分布
        category_counts = (
            Category.objects.annotate(count=Count("posts"))
            .values("name", "count")
            .order_by("-count")
        )
        context["category_labels"] = json.dumps([c["name"] for c in category_counts], ensure_ascii=False)
        context["category_data"] = json.dumps([c["count"] for c in category_counts])

        # 标签分布
        tag_counts = (
            Tag.objects.annotate(count=Count("posts"))
            .values("name", "count")
            .order_by("-count")[:10]
        )
        context["tag_labels"] = json.dumps([t["name"] for t in tag_counts], ensure_ascii=False)
        context["tag_data"] = json.dumps([t["count"] for t in tag_counts])

        # 系统信息
        try:
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            
            p = psutil.Process()
            uptime_seconds = timezone.now().timestamp() - p.create_time()
            uptime = timedelta(seconds=int(uptime_seconds))
            
            uptime_str = f"{uptime.days}{_('天')} " if uptime.days > 0 else ""
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str += f"{hours}{_('小时')} {minutes}{_('分钟')}"

            context["system_info"] = {
                "cpu_percent": cpu_usage,
                "memory_percent": memory.percent,
                "memory_used": memory.used,
                "memory_total": memory.total,
                "disk_percent": disk.percent,
                "disk_free": disk.free,
                "disk_total": disk.total,
                "python_version": platform.python_version(),
                "django_version": django.get_version(),
                "platform_system": platform.system(),
                "platform_release": platform.release(),
                "server_time": timezone.now(),
                "uptime": uptime_str,
            }
            context["system_health"] = int(max(0, 100 - max(cpu_usage, memory.percent, disk.percent)))
        except Exception:
            context["system_info"] = {}
            context["system_health"] = 85

        # 最近动态
        context["recent_comments"] = Comment.objects.select_related(
            "user", "post"
        ).order_by("-created_at")[:5]

        return context
