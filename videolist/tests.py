from django.test import TestCase, Client, AsyncClient
from django.urls import reverse
from .models import VideoSite
import json
from datetime import datetime
import asyncio

class VideoSiteModelTests(TestCase):
    def setUp(self):
        # 创建测试数据
        VideoSite.objects.create(
            name="测试影视站点",
            url="https://example.com/movie",
            description="这是一个测试影视站点",
            category="movie",
            is_invalid=False
        )
        
        VideoSite.objects.create(
            name="测试动漫站点",
            url="https://example.com/anime",
            description="这是一个测试动漫站点",
            category="anime",
            is_invalid=False
        )
        
        VideoSite.objects.create(
            name="无效站点",
            url="https://example.com/invalid",
            description="这是一个无效站点",
            category="movie",
            is_invalid=True
        )
    
    def test_videosite_str_representation(self):
        """测试 VideoSite 模型的字符串表示"""
        site = VideoSite.objects.get(name="测试影视站点")
        self.assertEqual(str(site), "测试影视站点")
    
    def test_videosite_category_choices(self):
        """测试分类选项是否正确"""
        site = VideoSite.objects.get(name="测试影视站点")
        self.assertEqual(site.get_category_display(), "影视")
        
        site = VideoSite.objects.get(name="测试动漫站点")
        self.assertEqual(site.get_category_display(), "动漫")
    
    def test_videosite_slug_generation(self):
        """测试 slug 自动生成"""
        site = VideoSite.objects.get(name="测试影视站点")
        self.assertEqual(site.slug, "ce-shi-ying-shi-zhan-dian")


class VideoSiteViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # 创建异步客户端
        cls.async_client = AsyncClient()
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
    
    def setUp(self):
        # 创建测试数据
        VideoSite.objects.create(
            name="测试影视站点",
            url="https://example.com/movie",
            description="这是一个测试影视站点",
            category="movie",
            is_invalid=False
        )
        
        VideoSite.objects.create(
            name="测试动漫站点",
            url="https://example.com/anime",
            description="这是一个测试动漫站点",
            category="anime",
            is_invalid=False
        )
        
        VideoSite.objects.create(
            name="无效站点",
            url="https://example.com/invalid",
            description="这是一个无效站点",
            category="movie",
            is_invalid=True
        )
        
        self.client = Client()
    
    async def test_index_view_async(self):
        """测试首页视图 (异步)"""
        response = await self.async_client.get(reverse('videolist:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'videolist/index.html')
    
    def test_index_view(self):
        """测试首页视图"""
        response = self.client.get(reverse('videolist:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'videolist/index.html')
        
    def test_site_list_api(self):
        """测试站点列表 API"""
        response = self.client.get(reverse('videolist:site_list'))
        self.assertEqual(response.status_code, 200)
        
        # 检查返回的 JSON 数据
        data = json.loads(response.content)
        self.assertEqual(len(data), 2)  # 应该只有 2 个有效站点
        
        # 测试分类过滤
        response = self.client.get(f"{reverse('videolist:site_list')}?category=movie")
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], "测试影视站点")
        
    def test_sitemap_view(self):
        """测试网站地图视图"""
        response = self.client.get(reverse('videolist:sitemap'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'videolist/sitemap.html')
        
        # 检查上下文数据
        self.assertEqual(len(response.context['movie_sites']), 1)
        self.assertEqual(len(response.context['anime_sites']), 1)
        
    def test_site_detail_view(self):
        """测试站点详情视图"""
        site = VideoSite.objects.get(name="测试影视站点")
        response = self.client.get(reverse('videolist:site_detail', args=[site.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'videolist/site_detail.html')
        
        # 检查上下文数据
        self.assertEqual(response.context['site'], site)
        
        # 测试无效站点 ID
        response = self.client.get(reverse('videolist:site_detail', args=[999]))
        self.assertEqual(response.status_code, 404)
        
        # 测试无效站点访问
        invalid_site = VideoSite.objects.get(name="无效站点")
        response = self.client.get(reverse('videolist:site_detail', args=[invalid_site.id]))
        self.assertEqual(response.status_code, 404)  # 应该返回 404

    def test_import_json_view(self):
        """测试 JSON 导入视图"""
        import_data = [
            {
                "name": "导入测试站点",
                "url": "https://example.com/import",
                "description": "这是一个通过导入创建的站点",
                "updateDate": "2024/4/25",
                "category": "anime"
            }
        ]
        
        response = self.client.post(
            reverse('videolist:import_json'),
            data=json.dumps(import_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # 验证导入是否成功
        imported_site = VideoSite.objects.filter(name="导入测试站点").first()
        self.assertIsNotNone(imported_site)
        self.assertEqual(imported_site.category, "anime")
        self.assertEqual(imported_site.url, "https://example.com/import")
        
        # 测试更新现有站点
        update_data = [
            {
                "name": "导入测试站点",
                "url": "https://example.com/updated",
                "description": "更新后的描述",
                "updateDate": "2024/4/26"
            }
        ]
        
        response = self.client.post(
            reverse('videolist:import_json'),
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # 验证更新是否成功
        updated_site = VideoSite.objects.get(name="导入测试站点")
        self.assertEqual(updated_site.url, "https://example.com/updated")
        self.assertEqual(updated_site.description, "更新后的描述")
        self.assertEqual(updated_site.category, "anime")  # 分类应保持不变
