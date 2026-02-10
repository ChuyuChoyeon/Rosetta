from django import forms
from django.utils.translation import gettext_lazy as _
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
from .mixins import StyleFormMixin
from ..services.tasks import get_registered_tasks
import json


class PeriodicTaskForm(StyleFormMixin, forms.ModelForm):
    """
    定时任务表单
    """

    # 调度类型选择器
    schedule_type = forms.ChoiceField(
        label=_("调度类型"),
        choices=[("interval", _("间隔调度")), ("crontab", _("Crontab 表达式"))],
        initial="interval",
        widget=forms.HiddenInput(),
        required=False,
    )

    # 间隔字段
    interval_every = forms.IntegerField(
        label=_("间隔数值"),
        min_value=1,
        initial=1,
        required=False,
        widget=forms.NumberInput(attrs={"class": "input input-bordered w-full"}),
    )
    interval_period = forms.ChoiceField(
        label=_("间隔单位"),
        choices=[
            ("days", _("天 (Days)")),
            ("hours", _("小时 (Hours)")),
            ("minutes", _("分钟 (Minutes)")),
            ("seconds", _("秒 (Seconds)")),
            ("microseconds", _("微秒 (Microseconds)")),
        ],
        initial="minutes",
        required=False,
        widget=forms.Select(attrs={"class": "select select-bordered w-full"}),
    )

    # Crontab 字段
    cron_minute = forms.CharField(
        label=_("分 (Minute)"),
        initial="*",
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "*", "class": "input input-bordered w-full"}
        ),
    )
    cron_hour = forms.CharField(
        label=_("时 (Hour)"),
        initial="*",
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "*", "class": "input input-bordered w-full"}
        ),
    )
    cron_day_of_week = forms.CharField(
        label=_("周 (Day of Week)"),
        initial="*",
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "*", "class": "input input-bordered w-full"}
        ),
    )
    cron_day_of_month = forms.CharField(
        label=_("日 (Day of Month)"),
        initial="*",
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "*", "class": "input input-bordered w-full"}
        ),
    )
    cron_month_of_year = forms.CharField(
        label=_("月 (Month of Year)"),
        initial="*",
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "*", "class": "input input-bordered w-full"}
        ),
    )

    class Meta:
        model = PeriodicTask
        fields = [
            "name",
            "task",
            "args",
            "kwargs",
            "queue",
            "priority",
            "expires",
            "one_off",
            "start_time",
            "enabled",
            "description",
        ]
        labels = {
            "name": _("任务名称"),
            "task": _("Task (注册路径)"),
            "args": _("位置参数 (Args)"),
            "kwargs": _("关键字参数 (Kwargs)"),
            "queue": _("队列 (Queue)"),
            "priority": _("优先级"),
            "expires": _("过期时间"),
            "one_off": _("仅运行一次"),
            "start_time": _("开始时间"),
            "enabled": _("启用"),
            "description": _("描述"),
        }
        widgets = {
            "description": forms.Textarea(
                attrs={"rows": 3, "class": "textarea textarea-bordered w-full"}
            ),
            "args": forms.Textarea(
                attrs={
                    "rows": 2,
                    "placeholder": "[]",
                    "class": "textarea textarea-bordered w-full font-mono",
                }
            ),
            "kwargs": forms.Textarea(
                attrs={
                    "rows": 2,
                    "placeholder": "{}",
                    "class": "textarea textarea-bordered w-full font-mono",
                }
            ),
            "start_time": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "input input-bordered w-full"}
            ),
            "expires": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "input input-bordered w-full"}
            ),
            "name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "queue": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "priority": forms.NumberInput(
                attrs={"class": "input input-bordered w-full"}
            ),
            "enabled": forms.CheckboxInput(attrs={"class": "toggle toggle-primary"}),
            "one_off": forms.CheckboxInput(
                attrs={"class": "checkbox checkbox-primary"}
            ),
        }
        help_texts = {
            "task": _(
                "选择要执行的 Celery 任务。您可以参考 'core.tasks' 中的示例任务。"
            ),
            "args": _("JSON 格式的位置参数列表 (例如 [1, 'arg'])"),
            "kwargs": _("JSON 格式的关键字参数字典 (例如 {'key': 'value'})"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 动态填充任务选择
        try:
            self.fields["task"].widget = forms.Select(
                choices=get_registered_tasks(),
                attrs={"class": "select select-bordered w-full"},
            )
        except Exception:
            # 如果 Celery 未运行或其他错误，回退到文本输入
            self.fields["task"].widget = forms.TextInput(
                attrs={"class": "input input-bordered w-full"}
            )

        instance = kwargs.get("instance")

        # 基于现有实例的初始值
        if instance:
            if instance.interval:
                self.fields["schedule_type"].initial = "interval"
                self.fields["interval_every"].initial = instance.interval.every
                self.fields["interval_period"].initial = instance.interval.period
            elif instance.crontab:
                self.fields["schedule_type"].initial = "crontab"
                self.fields["cron_minute"].initial = instance.crontab.minute
                self.fields["cron_hour"].initial = instance.crontab.hour
                self.fields["cron_day_of_week"].initial = instance.crontab.day_of_week
                self.fields["cron_day_of_month"].initial = instance.crontab.day_of_month
                self.fields[
                    "cron_month_of_year"
                ].initial = instance.crontab.month_of_year

    def clean_args(self):
        args = self.cleaned_data.get("args")
        if args:
            try:
                json_args = json.loads(args)
                if not isinstance(json_args, list):
                    raise forms.ValidationError(_("参数必须是列表格式 (List)"))
            except json.JSONDecodeError:
                raise forms.ValidationError(_("无效的 JSON 格式"))
        return args

    def clean_kwargs(self):
        kwargs = self.cleaned_data.get("kwargs")
        if kwargs:
            try:
                json_kwargs = json.loads(kwargs)
                if not isinstance(json_kwargs, dict):
                    raise forms.ValidationError(_("参数必须是字典格式 (Dict)"))
            except json.JSONDecodeError:
                raise forms.ValidationError(_("无效的 JSON 格式"))
        return kwargs

    def clean(self):
        cleaned_data = super().clean()
        schedule_type = cleaned_data.get("schedule_type")

        if schedule_type == "interval":
            every = cleaned_data.get("interval_every")
            period = cleaned_data.get("interval_period")
            if not every or not period:
                self.add_error("interval_every", _("请填写完整的间隔调度信息"))

        elif schedule_type == "crontab":
            # 可以在此添加基本验证
            pass

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        schedule_type = self.cleaned_data.get("schedule_type")

        if schedule_type == "interval":
            every = self.cleaned_data.get("interval_every")
            period = self.cleaned_data.get("interval_period")
            schedule, _ = IntervalSchedule.objects.get_or_create(
                every=every, period=period
            )
            instance.interval = schedule
            instance.crontab = None

        elif schedule_type == "crontab":
            minute = self.cleaned_data.get("cron_minute") or "*"
            hour = self.cleaned_data.get("cron_hour") or "*"
            day_of_week = self.cleaned_data.get("cron_day_of_week") or "*"
            day_of_month = self.cleaned_data.get("cron_day_of_month") or "*"
            month_of_year = self.cleaned_data.get("cron_month_of_year") or "*"

            from django.conf import settings

            timezone = (
                settings.CELERY_TIMEZONE
                if hasattr(settings, "CELERY_TIMEZONE")
                else "UTC"
            )

            schedule, _ = CrontabSchedule.objects.get_or_create(
                minute=minute,
                hour=hour,
                day_of_week=day_of_week,
                day_of_month=day_of_month,
                month_of_year=month_of_year,
                timezone=timezone,
            )
            instance.crontab = schedule
            instance.interval = None

        if commit:
            instance.save()
        return instance
