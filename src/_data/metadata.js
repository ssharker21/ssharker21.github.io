module.exports = function (configData) {
    let metadata = {
        "title": "summitsarkar",
        "url": "https://summitsarkar.com",
        "language": "en",
        "description": "Summit's personal website",
        "author": {
            "name": "Summit Sarkar",
            "email": "contact@summitsarkar.com"
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
