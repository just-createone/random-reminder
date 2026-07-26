const CACHE_NAME =
"random-reminder-v1";


const CACHE_FILES = [

    "/",

    "/index.html",

    "/css/style.css",

    "/js/api.js",

    "/js/ui.js",

    "/js/modal.js"

];



self.addEventListener(
"install",
(event)=>{


    event.waitUntil(

        caches.open(
            CACHE_NAME
        )
        .then(
            cache=>{

                return cache.addAll(
                    CACHE_FILES
                );

            }
        )

    );


});



self.addEventListener(
"fetch",
(event)=>{


    event.respondWith(

        caches.match(
            event.request
        )
        .then(
            response=>{

                return response ||
                    fetch(event.request);

            }
        )

    );


});