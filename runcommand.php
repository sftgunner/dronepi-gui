<?php

// Yes, I know this is 100% not the correct way of doing this

if (isset($_POST['command'])){
    if ($_POST['command'] == "test"){
        $output = passthru("python3 python/test.py");
        echo $output;
    }
    elseif ($_POST['command'] == "palette_fusion"){
        // $output = exec("v4l2-ctl -c lep_cid_vid_lut_select=1");
        exec('v4l2-ctl -c lep_cid_vid_lut_select=1 2>&1', $output);
        print_r($output);
        // echo $output; 
    }
    elseif ($_POST['command'] == "palette_icefire"){
        // $output = exec("v4l2-ctl -c lep_cid_vid_lut_select=1");
        exec('v4l2-ctl -c lep_cid_vid_lut_select=6 2>&1', $output);
        print_r($output);
        // echo $output; 
    }
    else{
        print_r($_POST);
    }
    // 
}
else{
    echo 'No command';
}

?>