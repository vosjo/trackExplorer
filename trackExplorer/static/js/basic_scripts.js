
function update_source(summary_source, track_source, grid_name, index) {

    if (selected_indices.length == 0){
        return;
    }

    file_name = summary_source.data['path'][selected_indices[0]];

    $( "#evolution_header" ).text('Evolution history: ' + file_name + ' (loading...)');

    var folder_name = '';
    if ('folder_name'+index in summary_source.data) {
        folder_name = summary_source.data['folder_name'+index][selected_indices[0]];
    }

    var model_folder_name = '';
    if ('model_folder_name'+index in summary_source.data) {
        model_folder_name = summary_source.data['model_folder_name'+index][selected_indices[0]];
    }

    $.ajax({
    url : "/history",
    type : "POST",
    data: JSON.stringify({
        grid_name: grid_name,
        file_name: file_name,
        folder_name: folder_name,
        model_folder_name: model_folder_name,
        history_pars: history_pars,
    }),
    dataType: "json",
    success : function(json) {

        for (var key in json) {
            track_source.data[key] = new Float64Array(json[key])
        }

        track_source.change.emit();

        if (json['x'].length == 0) {
            $( "#evolution_header" ).text('Evolution history: ' + file_name + ' (not found!)');
        } else {
            $( "#evolution_header" ).text('Evolution history: ' + file_name);
        }
    },
    error : function(xhr,errmsg,err) {
        console.log(xhr.status + ": " + xhr.responseText);

        $( "#evolution_header" ).text('Evolution history: ' + file_name + ' (failed!)');
    },
    });
    async: false;

};