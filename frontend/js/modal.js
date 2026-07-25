let modalResolve = null;


/**
 * 显示确认弹窗
 */
function showConfirmModal(message) {

    return new Promise((resolve) => {

        modalResolve = resolve;


        let modal =
            document.getElementById(
                "confirmModal"
            );


        if (!modal) {

            createModal();

            modal =
            document.getElementById(
                "confirmModal"
            );

        }


        document.getElementById(
            "confirmModalMessage"
        ).textContent =
            message;


        modal.classList.add(
            "show"
        );

    });

}


/**
 * 创建弹窗 DOM
 */
function createModal() {

    const div =
    document.createElement(
        "div"
    );


    div.id =
    "confirmModal";


    div.className =
    "modal";


    div.innerHTML = `

        <div class="modal-mask"></div>


        <div class="modal-box">


            <h3>
            确认操作
            </h3>


            <p id="confirmModalMessage">
            </p>


            <div class="modal-actions">


                <button
                onclick="closeConfirmModal(false)"
                >
                取消
                </button>



                <button
                class="danger-button"
                onclick="closeConfirmModal(true)"
                >
                删除
                </button>


            </div>


        </div>

    `;


    document.body.appendChild(
        div
    );

}



/**
 * 关闭确认弹窗
 */
function closeConfirmModal(result) {


    const modal =
    document.getElementById(
        "confirmModal"
    );


    modal.classList.remove(
        "show"
    );


    if(modalResolve){

        modalResolve(
            result
        );

        modalResolve = null;

    }

}