$(document).ready(function () {
    updateModelDropdown();
    updateTiffList();

    $('#modelFile').change(function () {
        $('#modelFileName').text(this.files[0]?.name || 'No file chosen');
    });

    $('#tiffFile').change(function () {
        $('#tiffFileName').text(this.files[0]?.name || 'No file chosen');
    });

    $('#modelForm').submit(function (e) {
        e.preventDefault();
        const formData = new FormData(this);
        $('#modelStatus').html('Uploading model...');
        $.ajax({
            url: '/upload_model',
            type: 'POST',
            data: formData,
            contentType: false,
            processData: false,
            success: function (res) {
                if (res.status === 'success') {
                    $('#modelStatus').text(res.message);
                    updateModelDropdown();
                    resetForm('modelForm');
                } else {
                    $('#modelStatus').text(res.message);
                }
            }
        });
    });

    $('#tiffForm').submit(function (e) {
        e.preventDefault();
        const formData = new FormData(this);
        $('#tiffStatus').html('Uploading TIFF...');
        $.ajax({
            url: '/upload_tiff',
            type: 'POST',
            data: formData,
            contentType: false,
            processData: false,
            success: function (res) {
                if (res.status === 'success') {
                    $('#tiffStatus').text(res.message);
                    updateTiffList();
                    resetForm('tiffForm');
                } else {
                    $('#tiffStatus').text(res.message);
                }
            }
        });
    });

    $('#predictionForm').submit(function (e) {
        e.preventDefault();
        const formData = $(this).serialize();
        $('#mapSection').hide();
        $.post('/predict', formData, function (res) {
            if (res.status === 'success') {
                $('#downloadTiffLink').attr('href', res.prediction_tiff).show();
                $('#predictionMap').html(`<iframe src="${res.map_html}" style="width:100%;height:500px;border:none;"></iframe>`);
                $('#mapSection').show();
            } else {
                alert('Error: ' + res.message);
            }
        });
    });

    function resetForm(formId) {
        $(`#${formId}`)[0].reset();
        if (formId === 'modelForm') $('#modelFileName').text('No file chosen');
        if (formId === 'tiffForm') {
            $('#tiffFileName').text('No file chosen');
            $('#tiffType').val('');
        }
    }

    function updateModelDropdown() {
        $.get('/list_models', function (data) {
            if (data.status === 'success') {
                const $select = $('#selectedModel');
                $select.empty().append('<option value="">-- Select a model --</option>');
                data.models.forEach(m => {
                    $select.append(`<option value="${m}">${m}</option>`);
                });
            }
        });
    }

    function updateTiffList() {
        $.get('/list_tiffs', function (data) {
            if (data.status === 'success') {
                const $list = $('#uploadedTiffs');
                $list.empty();
                if (Object.keys(data.tiffs).length === 0) {
                    $list.append('<p>No TIFF files uploaded yet</p>');
                    return;
                }
                const ul = $('<ul></ul>');
                for (const [key, val] of Object.entries(data.tiffs)) {
                    ul.append(`<li><strong>${key}</strong>: ${val}</li>`);
                }
                $list.append(ul);
            }
        });
    }
});
