from django.db import models
from django.urls import reverse

class VideoSite(models.Model):
    CATEGORY_CHOICES = [
        ('movie', '影视'),
        ('anime', '动漫'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="网站名称", db_index=True)
    url = models.URLField(verbose_name="网站地址")
    description = models.TextField(verbose_name="网站描述", blank=True)
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间", db_index=True)
    is_invalid = models.BooleanField(default=False, verbose_name="是否失效", db_index=True)
    view_count = models.PositiveIntegerField(default=0, verbose_name="浏览次数", db_index=True)
    category = models.CharField(
        max_length=10,
        choices=CATEGORY_CHOICES,
        default='movie',
        verbose_name="分类",
        db_index=True
    )

    class Meta:
        verbose_name = "视频网站"
        verbose_name_plural = "视频网站"
        ordering = ['-update_time']
        indexes = [
            models.Index(fields=['category', 'is_invalid']),
        ]

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('videolist:site_detail', args=[self.id])



        return f"{self.site.name} - {self.view_count} views"

class SiteView(models.Model):
    view_date = models.DateTimeField(auto_now_add=True, verbose_name="浏览日期")
    ip_address = models.GenericIPAddressField(verbose_name="IP地址", blank=True, null=True)
    user_agent = models.CharField(max_length=255, verbose_name="用户代理", blank=True, null=True)
    class Meta:
        verbose_name = "网站访问记录"
    