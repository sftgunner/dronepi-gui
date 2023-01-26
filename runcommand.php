<?php

// Yes, I know this is 100% not the correct way of doing this

if (isset($_POST['command'])){
    if ($_POST['command'] == "test"){
        $output = passthru("python3 python/test.py");
        echo $output;
    }
    elseif ($_POST['command'] == "camerapalette"){
        $output = exec("v4l2-ctl -c lep_cid_vid_lut_select=1");
        echo $output;
        // echo "palette";
    }
    else{
        print_r($_POST);
    }
    // 
}
else{
    echo 'No command';
    $output = exec("ping 1.1.1.1 -t 1");
    echo $output;
}

?>