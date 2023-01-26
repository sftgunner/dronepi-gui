<?php

// Yes, I know this is 100% not the correct way of doing this

if (isset($_GET['command'])){

if ($_GET['command'] == "test"){

$output = passthru("python3 python/test.py");

}
}
else{
    echo 'No command';
}

?>