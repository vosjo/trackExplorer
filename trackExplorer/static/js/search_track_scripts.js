
function download_source(grid_name, track_name, file_type) {

    $.post(
        "/download_history",
        JSON.stringify({
        grid_name: grid_name,
        file_name: track_name,
        file_type: file_type,
        }),
        function(retData) {
            console.log('success in downloading file');
            $("body").append("<iframe src='" + retData.url + "' style='display: none;' ></iframe>");
        }
    );

};