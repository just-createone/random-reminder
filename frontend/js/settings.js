/**
 * 页面加载时读取设置
 */
async function loadSettings(){


    try{


        const result =
        await apiGet(
            "/api/settings"
        );


        const settings =
        result.data;



        document.getElementById(
            "enabled"
        ).checked =
        settings.enabled;



        document.getElementById(
            "allDay"
        ).checked =
        settings.all_day;



        document.getElementById(
            "rangeTime"
        ).checked =
        !settings.all_day;



        document.getElementById(
            "startTime"
        ).value =
        settings.start_time || "";



        document.getElementById(
            "endTime"
        ).value =
        settings.end_time || "";



        document.getElementById(
            "timesPerDay"
        ).value =
        settings.times_per_day;



        document.getElementById(
            "minimumInterval"
        ).value =
        settings.minimum_interval;



        updateTimeRangeVisibility();



    }catch(error){


        alert(
            error.message
        );

    }


}





/**
 * 保存设置
 */
async function saveSettings(){


    const allDay =
        document.getElementById(
            "allDay"
        ).checked;



    const data = {


        enabled:
        document.getElementById(
            "enabled"
        ).checked,


        all_day:
        allDay,


        start_time:
        allDay
        ?
        null
        :
        document.getElementById(
            "startTime"
        ).value,


        end_time:
        allDay
        ?
        null
        :
        document.getElementById(
            "endTime"
        ).value,


        times_per_day:
        Number(
            document.getElementById(
                "timesPerDay"
            ).value
        ),


        minimum_interval:
        Number(
            document.getElementById(
                "minimumInterval"
            ).value
        )

    };



    try{


        await apiPut(
            "/api/settings",
            data
        );


        alert(
            "设置保存成功"
        );



    }catch(error){


        alert(
            error.message
        );

    }


}





/**
 * 控制时间输入框显示
 */
function updateTimeRangeVisibility(){


    const allDay =
    document.getElementById(
        "allDay"
    ).checked;



    const container =
    document.getElementById(
        "timeRangeContainer"
    );



    container.style.display =
    allDay
    ?
    "none"
    :
    "block";


}




document
.querySelectorAll(
    "input[name='timeMode']"
)
.forEach(
    item => {


        item.addEventListener(
            "change",
            updateTimeRangeVisibility
        );


    }
);



loadSettings();