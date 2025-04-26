from django.db import models

class VideoSite(models.Model):
    CATEGORY_CHOICES = [
        ('movie', '影视'),
        ('anime', '动漫'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="网站名称")
    url = models.URLField(verbose_name="网站地址")
    description = models.TextField(verbose_name="网站描述")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    is_invalid = models.BooleanField(default=False, verbose_name="是否失效")
    category = models.CharField(
        max_length=10,
        choices=CATEGORY_CHOICES,
        default='movie',
        verbose_name="分类"
    )

    class Meta:
        verbose_name = "视频网站"
        verbose_name_plural = "视频网站"

    def __str__(self):
        return self.name
