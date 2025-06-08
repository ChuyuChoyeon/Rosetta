"""
UNFOLD 管理界面的配置设置
"""

from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

# UNFOLD 配置
UNFOLD = {
    "SITE_TITLE": "Rosetta 管理系统",
    "SITE_HEADER": "Rosetta",
    "SITE_SUBHEADER": "Rosetta",
    "SITE_URL": "/",
    "SITE_SYMBOL": "book",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "SHOW_BACK_BUTTON": True,
    "BORDER_RADIUS": "6px",
    "STYLES": [
        lambda request: static("css/custom.css"),
    ],
    "COLORS": {
        "primary": {
            "50": "250 245 255",
            "100": "243 232 255",
            "200": "233 213 255",
            "300": "216 180 254",
            "400": "192 132 252",
            "500": "168 85 247",
            "600": "147 51 234",
            "700": "126 34 206",
            "800": "107 33 168",
            "900": "88 28 135",
            "950": "59 7 100",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "内容管理",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "视频网站",
                        "icon": "video_library",
                        "model": "videolist.videosite",
                        "link": reverse_lazy("admin:videolist_videosite_changelist"),
                    },
                    {
                        "title": "网站访问记录",
                        "icon": "history",
                        "model": "videolist.siteview",
                        "link": reverse_lazy("admin:videolist_siteview_changelist"),
                    },
                    {
                        "title": "标签管理",
                        "icon": "label",
                        "model": "taggit.tag",
                        "link": reverse_lazy("admin:taggit_tag_changelist"),
                    }

                ],
            },
            # {
            #     "title": "博客管理",
            #     "separator": True,
            #     "items": [
            #         {
            #             "title": "文章",
            #             "icon": "article",
            #             "link": "/admin/blog/post/",
            #         },
            #         {
            #             "title": "分类",
            #             "icon": "category",
            #             "link": "/admin/blog/category/",
            #         },
            #     ],
            # },
            {
                "title": "系统管理",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "导航管理",
                        "icon": "menu",
                        "model": "navigation.navigationitem",
                        "link": reverse_lazy("admin:navigation_navigationitem_changelist"),
                    },
                    {
                        "title": "用户管理",
                        "icon": "people",
                        "model": "auth.user",
                        "link": reverse_lazy("admin:auth_user_changelist"),
                    },
                    {
                        "title": "用户组管理",
                        "icon": "group",
                        "model": "auth.group",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            },
        ],
    },
    "EXTENSIONS": {
        "modeltranslation": {
            "enabled": False,
            "flags": {}
        },
    },
    "TABS": [],
    "USE_TRANSLATIONS": True,
    # Unfold 最新版本支持的配置
    "ENVIRONMENT": {
        "name": "开发环境" if __import__('django.conf').conf.settings.DEBUG else "生产环境",
        "color": "blue" if __import__('django.conf').conf.settings.DEBUG else "red",
        "badge": True,
    },
}
