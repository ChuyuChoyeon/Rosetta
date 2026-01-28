
@login_required
@require_POST
def toggle_pin_post(request, pk):
    """
    切换文章置顶状态
    """
    if not request.user.is_staff:
        return HttpResponseForbidden("您没有权限执行此操作")
    
    post = get_object_or_404(Post, pk=pk)
    post.is_pinned = not post.is_pinned
    post.save(update_fields=["is_pinned"])
    
    # 返回新的按钮状态 (HTMX)
    btn_class = "text-yellow-500" if post.is_pinned else "text-gray-400 hover:text-yellow-500"
    icon_fill = "fill-current" if post.is_pinned else "fill-none"
    
    # 这里我们返回一个简单的 SVG 图标，或者让前端根据状态类刷新
    # 既然是 shortcut operation，我们直接返回 button 的 HTML
    
    return render(request, "blog/partials/pin_button.html", {"post": post})
