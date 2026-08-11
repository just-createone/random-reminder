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


        showMessage(
            "暂时无法加载设置，请稍后重试。",
            "error"
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


        showMessage(
            "设置保存成功"
        );



    }catch(error){


        showMessage(
    "保存设置失败，请稍后重试。",
    "error"
);

    }


}





/**
 * 导出用户数据为 JSON 文件。
 */
async function exportUserData(){


    const button =
    document.getElementById(
        "exportDataButton"
    );


    button.disabled = true;


    try{


        const result =
        await apiGet(
            "/api/data/export"
        );


        const blob = new Blob(
            [JSON.stringify(result.data, null, 2)],
            {type: "application/json"}
        );


        const downloadUrl =
        URL.createObjectURL(blob);


        const link =
        document.createElement("a");


        link.href = downloadUrl;
        link.download =
        `random-reminder-export-${new Date().toISOString().slice(0, 10)}.json`;


        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(downloadUrl);


        showMessage("数据导出成功");


    }catch(error){


        console.error("导出数据失败", error);


        showMessage(
            "导出数据失败，请稍后重试。",
            "error"
        );


    }finally{


        button.disabled = false;


    }


}



/**
 * 更新当前选择的导入文件状态。
 */
function updateImportFileState(){


    const fileInput =
    document.getElementById(
        "importDataFile"
    );


    const fileName =
    document.getElementById(
        "importDataFileName"
    );


    const importButton =
    document.getElementById(
        "importDataButton"
    );


    const file = fileInput.files[0];


    fileName.textContent =
    file
    ?
    `已选择：${file.name}`
    :
    "尚未选择文件";


    importButton.disabled = !file;


}



/**
 * 导入用户选择的 JSON 数据文件。
 */
async function importUserData(){


    const fileInput =
    document.getElementById(
        "importDataFile"
    );


    const importButton =
    document.getElementById(
        "importDataButton"
    );


    const file = fileInput.files[0];


    if(!file){


        showMessage(
            "请先选择要导入的 JSON 文件。",
            "error"
        );


        return;


    }


    let payload;


    try{


        payload = JSON.parse(
            await file.text()
        );


    }catch(error){


        console.error("读取导入文件失败", error);


        showMessage(
            "导入文件不是有效的 JSON，请选择正确的导出文件。",
            "error"
        );


        return;


    }


    const confirmed =
    await showConfirmModal(
        "导入会保留当前提醒、追加文件中的提醒，并恢复文件中的提醒设置。是否继续？",
        "导入"
    );


    if(!confirmed){


        return;


    }


    importButton.disabled = true;


    try{


        const result =
        await apiPost(
            "/api/data/import",
            payload
        );


        const importedReminders =
        result.data.imported_reminders;


        showMessage(
            `成功导入 ${importedReminders} 条提醒，并恢复提醒设置。`
        );


        fileInput.value = "";
        updateImportFileState();
        await loadSettings();


    }catch(error){


        console.error("导入数据失败", error);


        showMessage(
            "导入数据失败，请确认文件有效后重试。",
            "error"
        );


        importButton.disabled = false;


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



document.getElementById(
    "exportDataButton"
).addEventListener(
    "click",
    exportUserData
);


document.getElementById(
    "importDataFile"
).addEventListener(
    "change",
    updateImportFileState
);


document.getElementById(
    "importDataButton"
).addEventListener(
    "click",
    importUserData
);


loadSettings();
