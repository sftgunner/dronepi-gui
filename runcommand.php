<?php

// Yes, I know this is 100% not the correct way of doing this

if (isset($_POST['command'])){
    if ($_POST['command'] == "test"){
        $output = passthru("python3 python/test.py");
    }
    elseif ($_POST['command'] == "camerapalette"){
        $output = passthru("v4l2-ctl -c lep_cid_vid_lut_select=1");
    }
    echo $output;
}
else{
    echo 'No command';
}

?>