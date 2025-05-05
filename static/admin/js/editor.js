document.addEventListener('DOMContentLoaded', function() {
    // 获取文本区域元素
    const bodyField = document.getElementById('id_body');
    if (!bodyField) return;
    
    // 创建一个容器来放置编辑器
    const editorContainer = document.createElement('div');
    editorContainer.id = 'editorjs';
    editorContainer.style.minHeight = '400px';
    editorContainer.style.border = '1px solid #ddd';
    editorContainer.style.borderRadius = '4px';
    editorContainer.style.marginTop = '10px';
    editorContainer.style.backgroundColor = '#fff';
    
    // 在文本区域之后插入编辑器容器
    bodyField.parentNode.insertBefore(editorContainer, bodyField.nextSibling);
    
    // 隐藏原始文本区域，但保留它用于表单提交
    bodyField.style.display = 'none';
    
    // 如果有已有内容，尝试解析为JSON，否则作为Markdown处理
    let initialData = {};
    try {
        if (bodyField.value) {
            // 检查是否是JSON格式
            JSON.parse(bodyField.value);
            initialData = JSON.parse(bodyField.value);
        }
    } catch (e) {
        // 不是JSON格式，处理为Markdown内容
        initialData = {
            blocks: [{
                type: 'paragraph',
                data: {
                    text: bodyField.value
                }
            }]
        };
    }
    
    // 初始化Editor.js
    const editor = new EditorJS({
        holder: 'editorjs',
        autofocus: true,
        placeholder: '开始编写文章内容...',
        tools: {
            header: Header,
            list: List,
            code: CodeTool,
            quote: Quote,
            marker: Marker,
            image: {
                class: ImageTool,
                config: {
                    endpoints: {
                        byFile: '/admin/blog/post/upload-image/',
                    }
                }
            }
        },
        data: initialData,
        onChange: function() {
            editor.save().then((outputData) => {
                bodyField.value = JSON.stringify(outputData);
            });
        }
    });
    
    // 表单提交前确保内容已保存到原始字段
    bodyField.form.addEventListener('submit', function(event) {
        event.preventDefault();
        editor.save().then((outputData) => {
            bodyField.value = JSON.stringify(outputData);
            this.submit();
        });
    });
});
