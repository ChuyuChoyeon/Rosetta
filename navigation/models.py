from django.db import models
from django.utils.translation import gettext_lazy as _

class NavigationItem(models.Model):
    """网站导航项模型"""
    title = models.CharField(_('标题'), max_length=50)
    url = models.CharField(_('链接'), max_length=200)
    icon = models.CharField(_('图标'), max_length=50, blank=True, 
                          help_text=_('Font Awesome 图标类名，例如: fas fa-home'))
    order = models.PositiveSmallIntegerField(_('排序'), default=0)
    is_active = models.BooleanField(_('启用'), default=True)
    target_blank = models.BooleanField(_('新窗口打开'), default=False)
    parent = models.ForeignKey('self', verbose_name=_('父级菜单'), 
                              null=True, blank=True, 
                              on_delete=models.SET_NULL,
                              related_name='children')
    
    class Meta:
        verbose_name = _('导航项')
        verbose_name_plural = _('导航项')
        ordering = ['order', 'id']
    
    def __str__(self):
        return self.title
