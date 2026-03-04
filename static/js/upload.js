document.getElementById('upload-button').addEventListener('click', function() {
    var fileInput = document.getElementById('file-input');
    var file = fileInput.files[0];
    var formData = new FormData();
    console.log('上传的文件名:', file.name);

    formData.append('file', file);

    fetch('/upload_file', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // 处理上传的原始图片
        var img_original = document.getElementById('original-img');
        var timeStamp_original = new Date().getTime();
        var newOriginalImageUrl = data.originalImageUrl + "?t=" + timeStamp_original;
        img_original.src = newOriginalImageUrl;

        // 处理上传的处理后图片
        var img_processed = document.getElementById('processed-img');
        var timeStamp_processed = new Date().getTime();
        var newProcessedImageUrl = data.processedImageUrl + "?t=" + timeStamp_processed;
        img_processed.src = newProcessedImageUrl;
    });
});

