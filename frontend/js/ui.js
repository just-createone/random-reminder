let messageTimer = null;


/**
 * 显示页面消息提示
 */
function showMessage(
    message,
    type = "success"
){

    let container =
        document.getElementById(
            "globalMessage"
        );


    if(!container){

        container =
        document.createElement(
            "div"
        );


        container.id =
        "globalMessage";


        container.className =
        "global-message";


        document.body.appendChild(
            container
        );

    }


    container.textContent =
        message;


    container.className =
        `global-message ${type} show`;



    if(messageTimer){

        clearTimeout(
            messageTimer
        );

    }


    messageTimer =
    setTimeout(
        ()=>{

            container.className =
            "global-message";

        },
        4000
    );

}