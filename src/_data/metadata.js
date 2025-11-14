module.exports = function (configData) {
    let metadata = {
        "title": "CGM",
        "url": "https://colegm.com",
        "language": "en",
        "description": "Cole's personal website",
        "author": {
            "name": "Cole Graber-Mitchell",
            "email": "website@colegm.com"
        },
        "feedUrl": "https://colegm.com/feed.xml"
    };

    let dev = {
        "title": "DEV - CGM",
        "url": "http://localhost:8080"
    }

    if (configData.eleventy.env.runMode === "serve") {
        return Object.assign({}, metadata, dev);
    } else {
        return metadata;
    }
};