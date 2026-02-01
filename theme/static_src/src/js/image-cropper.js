import Cropper from 'cropperjs';
// import 'cropperjs/dist/cropper.css'; // Imported in base template to avoid side-effect warnings

/**
 * Global Image Cropper for Alpine.js
 * Automatically injects modal and provides reusable data component.
 */

// Global function to inject modal
window.injectCropperModal = function() {
    // Check if modal already exists
    if (document.getElementById('global_cropper_modal')) return;

    // Check if body exists (should be always true when called)
    if (!document.body) {
        requestAnimationFrame(window.injectCropperModal);
        return;
    }

    const modalHtml = `
    <dialog id="global_cropper_modal" class="modal" style="z-index: 99999;">
        <div class="modal-box w-11/12 max-w-5xl h-[80vh] flex flex-col p-0 bg-base-100 rounded-xl overflow-hidden shadow-2xl">
            <div class="flex justify-between items-center p-4 border-b border-base-200 bg-base-100 z-10">
                <h3 class="font-bold text-lg flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">crop</span>
                    裁剪图片
                </h3>
                <button type="button" class="btn btn-sm btn-circle btn-ghost" id="cropper_close_btn">✕</button>
            </div>
            
            <div class="flex-1 bg-neutral/90 relative overflow-hidden flex items-center justify-center p-4">
                    <img id="global_cropper_image" class="max-w-full max-h-full block opacity-0 transition-opacity duration-300" src="">
            </div>
            
            <div class="p-4 border-t border-base-200 flex justify-between items-center bg-base-100 z-10">
                <div class="flex gap-2">
                    <button type="button" class="btn btn-sm btn-square btn-ghost tooltip tooltip-right" data-tip="向左旋转" id="cropper_rotate_left">
                        <span class="material-symbols-outlined">rotate_left</span>
                    </button>
                    <button type="button" class="btn btn-sm btn-square btn-ghost tooltip tooltip-right" data-tip="向右旋转" id="cropper_rotate_right">
                        <span class="material-symbols-outlined">rotate_right</span>
                    </button>
                    <button type="button" class="btn btn-sm btn-square btn-ghost tooltip tooltip-right" data-tip="重置" id="cropper_reset">
                        <span class="material-symbols-outlined">restart_alt</span>
                    </button>
                </div>
                <div class="flex gap-3">
                    <button type="button" class="btn btn-ghost" id="cropper_cancel">取消</button>
                    <button type="button" class="btn btn-primary px-6 gap-2" id="cropper_save">
                        <span class="material-symbols-outlined text-lg">check</span>
                        确定
                    </button>
                </div>
            </div>
        </div>
        <form method="dialog" class="modal-backdrop">
            <button type="button" id="cropper_backdrop">close</button>
        </form>
    </dialog>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHtml);
};

// Inject on load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', window.injectCropperModal);
} else {
    window.injectCropperModal();
}

// Re-inject after HTMX swap (fixes missing modal on navigation)
document.addEventListener('htmx:afterSwap', function(event) {
    window.injectCropperModal();
});

// Also try to inject when Alpine component initializes (as a fallback)
document.addEventListener('alpine:init', () => {
    Alpine.data('imageCropper', (config = {}) => ({
        previewUrl: config.previewUrl || null,
        cropper: null,
        aspectRatio: config.aspectRatio || 16/9,
        originalFile: null,
        
        init() {
            // Ensure modal exists
            if (typeof window.injectCropperModal === 'function') {
                window.injectCropperModal();
            }
        },

        handleFile(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            // Check file type
            if (!file.type.startsWith('image/')) {
                alert('请上传图片文件');
                return;
            }

            this.originalFile = file;
            const reader = new FileReader();
            reader.onload = (e) => {
                this.openCropper(e.target.result, event.target);
            };
            reader.readAsDataURL(file);
            
            // Clear input value to allow selecting same file again if canceled
            event.target.value = '';
        },

        openCropper(imageUrl, inputElement) {
            // Ensure modal exists before trying to access it
            if (typeof window.injectCropperModal === 'function') {
                window.injectCropperModal();
            }

            const modal = document.getElementById('global_cropper_modal');
            const image = document.getElementById('global_cropper_image');
            const closeBtn = document.getElementById('cropper_close_btn');
            const backdrop = document.getElementById('cropper_backdrop');
            const cancelBtn = document.getElementById('cropper_cancel');
            const saveBtn = document.getElementById('cropper_save');
            const rotateLeft = document.getElementById('cropper_rotate_left');
            const rotateRight = document.getElementById('cropper_rotate_right');
            const resetBtn = document.getElementById('cropper_reset');

            if (!modal || !image) {
                console.error('Cropper modal elements not found!');
                return;
            }

            image.src = imageUrl;
            image.style.opacity = '0'; // Hide until cropper ready
            
            modal.showModal();

            // Destroy previous instance
            if (window.globalCropperInstance) {
                window.globalCropperInstance.destroy();
            }

            // Initialize Cropper
            window.globalCropperInstance = new Cropper(image, {
                aspectRatio: this.aspectRatio,
                viewMode: 1,
                dragMode: 'move',
                autoCropArea: 0.8,
                restore: false,
                guides: true,
                center: true,
                highlight: false,
                cropBoxMovable: true,
                cropBoxResizable: true,
                toggleDragModeOnDblclick: false,
                ready() {
                    image.style.opacity = '1';
                }
            });

            // Bind Events
            const closeHandler = () => {
                modal.close();
                if (window.globalCropperInstance) {
                    window.globalCropperInstance.destroy();
                    window.globalCropperInstance = null;
                }
            };

            const saveHandler = () => {
                if (!window.globalCropperInstance) return;
                
                // Get cropped canvas
                const canvas = window.globalCropperInstance.getCroppedCanvas({
                    maxWidth: 4096,
                    maxHeight: 4096,
                    fillColor: '#fff',
                });

                canvas.toBlob((blob) => {
                    if (!blob) return;

                    // Create new File
                    const newFile = new File([blob], this.originalFile.name, {
                        type: this.originalFile.type,
                        lastModified: new Date().getTime()
                    });

                    // Update DataTransfer
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(newFile);
                    inputElement.files = dataTransfer.files;

                    // Update Preview
                    this.previewUrl = URL.createObjectURL(blob);

                    closeHandler();
                }, this.originalFile.type);
            };

            // Remove old listeners to prevent stacking
            const newSaveBtn = saveBtn.cloneNode(true);
            saveBtn.parentNode.replaceChild(newSaveBtn, saveBtn);
            
            const newCloseBtn = closeBtn.cloneNode(true);
            closeBtn.parentNode.replaceChild(newCloseBtn, closeBtn);
            
            const newCancelBtn = cancelBtn.cloneNode(true);
            cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);

            const newBackdrop = backdrop.cloneNode(true);
            backdrop.parentNode.replaceChild(newBackdrop, backdrop);

            // Rotation buttons
            rotateLeft.onclick = () => window.globalCropperInstance?.rotate(-90);
            rotateRight.onclick = () => window.globalCropperInstance?.rotate(90);
            resetBtn.onclick = () => window.globalCropperInstance?.reset();

            // Bind new listeners
            newCloseBtn.addEventListener('click', closeHandler);
            newCancelBtn.addEventListener('click', closeHandler);
            newBackdrop.addEventListener('click', closeHandler);
            newSaveBtn.addEventListener('click', saveHandler);
        }
    }));
});
