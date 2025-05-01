from django.db import models
from django.core.exceptions import ValidationError

class Profile(models.Model):
    """个人资料模型"""
    name = models.CharField(max_length=50, verbose_name="姓名")
    title = models.CharField(max_length=100, verbose_name="职位头衔")
    avatar = models.ImageField(upload_to='avatars/', verbose_name="头像")
    about_me = models.TextField(verbose_name="关于我")
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if Profile.objects.exists() and not self.pk:
            # 确保只有一条记录
            raise ValidationError('只能创建一个个人资料')
        return super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "个人资料"
        verbose_name_plural = verbose_name

class Skill(models.Model):
    """技能标签模型"""
    name = models.CharField(max_length=50, verbose_name="名称")
    color_choices = [
        ('blue', '蓝色'),
        ('green', '绿色'),
        ('purple', '紫色'),
        ('red', '红色'),
        ('yellow', '黄色'),
        ('pink', '粉色'),
        ('indigo', '靛蓝'),
        ('gray', '灰色'),
        ('teal', '蓝绿'),
        ('orange', '橙色'),
        ('cyan', '青色'),
        ('lime', '石灰'),
        ('amber', '琥珀'),
        ('emerald', '祖母绿'),
        ('fuchsia', '紫红'),
        ('rose', '玫瑰'),
        ('sky', '天蓝'),
        ('violet', '紫罗兰'),
    ]
    color = models.CharField(max_length=20, choices=color_choices, default='blue', verbose_name="颜色")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="排序")
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['order']
        verbose_name = "技能标签"
        verbose_name_plural = verbose_name

class Link(models.Model):
    """链接模型"""
    name = models.CharField(max_length=50, verbose_name="名称")
    url = models.CharField(max_length=255, verbose_name="链接地址",
                        help_text="可以是完整URL(如https://example.com)或相对路径(如vl/)")
    is_relative = models.BooleanField(default=False, verbose_name="相对路径",
                                   help_text="勾选表示链接是相对于当前域名的路径")
    username = models.CharField(max_length=100, verbose_name="用户名", blank=True)
    icon = models.CharField(max_length=50, verbose_name="图标类名", 
                           help_text="Font Awesome图标类名，如 fa-github、fa-linkedin 等")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="排序")
    is_navigation = models.BooleanField(default=False, verbose_name="导航链接", 
                                      help_text="是否显示在导航栏上方")
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['order']
        verbose_name = "链接"
        verbose_name_plural = verbose_name

class Contact(models.Model):
    TAILWIND_COLOR_CHOICES = [
        ('blue', '蓝色 (bg-blue-500)'),
        ('red', '红色 (bg-red-500)'),
        ('green', '绿色 (bg-green-500)'),
        ('yellow', '黄色 (bg-yellow-500)'),
        ('purple', '紫色 (bg-purple-500)'),
        ('pink', '粉色 (bg-pink-500)'),
        ('indigo', '靛蓝 (bg-indigo-500)'),
        ('gray', '灰色 (bg-gray-500)'),
        ('teal', '蓝绿 (bg-teal-500)'),
        ('orange', '橙色 (bg-orange-500)'),
        ('cyan', '青色 (bg-cyan-500)'),
        ('lime', '石灰 (bg-lime-500)'),
        ('amber', '琥珀 (bg-amber-500)'),
        ('emerald', '祖母绿 (bg-emerald-500)'),
        ('fuchsia', '紫红 (bg-fuchsia-500)'),
        ('rose', '玫瑰 (bg-rose-500)'),
        ('sky', '天蓝 (bg-sky-500)'),
        ('violet', '紫罗兰 (bg-violet-500)'),
    ]
    
    method = models.CharField(max_length=50, verbose_name="联系方式")
    value = models.CharField(max_length=100, verbose_name="联系值")
    icon = models.CharField(max_length=50, verbose_name="图标类名",
                          help_text="Font Awesome图标类名，如 fa-envelope、fa-phone、fa-weixin 等")
    color = models.CharField(max_length=20, choices=TAILWIND_COLOR_CHOICES, 
                           default='blue', verbose_name="颜色")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="排序")
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['order']
        verbose_name = "联系方式"
        verbose_name_plural = verbose_name
