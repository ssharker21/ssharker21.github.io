---
title: Working with service workers
date: 2017-07-30
---

Recently I decided to procrastinate working on actual work (projects for school and Pupil) and remake my old jekyll website to something that was less work to maintain and that I actually understood.
Hence, [metalsmith](http://metalsmith.io).
It's a static site generator written in Node.js that uses a series of transforms on files to ultimately produce the end result.
There was somewhat of a learning curve associated with the new tool and language (javascript is new for me), but in a later blog post I'll talk about metalsmith.
This one is going to be mostly a discussion about speed.

My primary concern was speed.
I wanted to make this website fast.
__Really fast__.
This post is intended to be a short writeup of my efforts.

{{< a2 "Sending less stuff" >}}

The first part of making a fast website is reducing the bytes that are sent to the browser.
This meant keeping my pages small and my styles lightweight.
My main handlebars layout (read: base html) is only 50 lines of html, including the header, navigation, and footer.

I started with a few styles based on readability from [this wonderfully named website](https://thebestmotherfucking.website/) and then expanded from there to fit my site.
I'm not using any frameworks or resets, so there are no unused styles.
This also makes designing my html easier, especially for such a simple site.
I'm not against frameworks, but for raw speed, I've found it's best to write my own styles.

For example, the css stylesheet is a mere 2.01 kb when minified.
In comparison, this text is a whole order of magnitude more than that. 
All of the resources are also minified along the metalsmith pipeline to make sure that the minimum number of bytes possible are sent.

Despite using no responsive web framework, the site works on all reasonably-sized devices simply by reflowing the text.
I used a single media query to make the navigation links work better.
There is one caveat: the header ascii art won't change sizes to fit the viewport so on devices with less than 400 pixels of width it can cause horizontal scrolling to occur.
I could've fixed this with javascript, but I decided it wasn't worth it for the extra bytes and time to paint.

Additionally, the index page has no synchronous external resources to load before it can paint!
It uses the same css and javascript as the other pages, except they are inlined automatically to make the page load with one request.
There is a metalsmith plugin that does this for me, so it took me almost no effort to include.
There are no web fonts loaded, no images, no jQuery: in essence, nothing but what is necessary is even included.

There is one problem with inlining resources on the index page: the browser HTTP cache doesn't get to cache them for future page loads, and I'd rather sacrifice initial page load time in order to make movement throughout the site fluid.
Thankfully, we can get the best of both worlds!
In order to fix this, the site installs a service worker on supported browsers to cache the stylesheet and javascript before they're needed.

{{< a2 "Caching certain resources" >}}

[Service workers](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API) are a relatively new spec, even with the fast pace of web development.
They are simply javascript that runs in between the browser and any remote requests made by a webpage.
They can cache resources on install and can also cache resources on the fly.
This website does both.

As a quick primer on service workers, one of their primary uses is responding to `onfetch` events with a custom response for a given request.
Often, this response is from the ServiceWorker cache.
They cannot access the DOM, as they run in their own context, but they can pass messages between pages of the website and receive messages from and send messages to a given page.
More complicated service workers can receive push notifications from the server, show them to the user, and wake up at certain times to update caches.
They're new, but very powerful.

Copying almost wholesale from [the offline cookbook](https://jakearchibald.com/2014/offline-cookbook/), the service worker for this website only does a small subset of what is possible.

{{< a3 "Installation: the first step" >}}

Here's installation code, which preloads the cache with some resources that are needed.
```javascript
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE).then(function(cache) {
      console.log("[install] successfully running and cache opened to preload");
      return cache.addAll([
        '/js/app.js',
        '/css/main.css',
        '/css/highlight-default.css',
        '/offline/index.html'
      ]);
    }).then(function() {
      console.log("[install] cache preloaded");
      self.skipWaiting();
    })
  );
});
```

The main section of this code is `cache.addAll([...])`: it loads the javascript, the main stylesheet, and the stylesheet for code highlighting.

If you aren't familiar with javascript, [Promises](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise) are a key new language feature that underpin much of the new [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API).
Basically, a Promise is exactly what it sounds like: a promise of a value, sometime in the future.
They can 'reject' or 'resolve,' giving a value on a resolve and some error or reason on a reject.
I'm still trying to figure out exactly how to use them, but they're a nice abstraction allowing asynchronous code to be written without crazy callbacks.
In this code sample, you can see them in a bunch of places.
In particular, `caches.open(CACHE)` returns a Promise, which could be the only part of the argument to `event.waitUntil`.
However, I don't just want to open the cache; I want to add things to it.

To accomplish that, I can transform that Promise (a promise of a cache) into another Promise by chaining `.then(function)` onto it.
That function argument must return another promise: in this case, `cache.addAll([...])` returns a promise of adding resources to the cache.
Next I transform that promise into another, calling `self.skipWaiting()` to immediately take control of the page instead of waiting for a navigation event (in conjunction with `self.clients.claim()`).

(Actually, this might be a lie. `.then()` can also be used to just run further code after a Promise resolves, and in this case that's what is used for. However, it seems to me to be more correct to call it a 'transform.')

See, that's not so hard!
Of course, at this point, the service worker hasn't actually done anything useful yet: it still can't respond to requests.

{{< a3 Working as a cache >}}

To act as a cache in between requests and the Internet, the service worker needs to register to receive and process `onfetch` events.
```javascript
self.addEventListener('fetch', function(event) {
  event.respondWith(
    caches.open(CACHE).then(cache => {
      return promiseAny([
        cache.match(event.request).then(response => {
          if(response) {
            return Promise.resolve(response);
          } else {
            return Promise.reject('not in cache');
          }
        }),
        fetch(event.request.clone()).then(response => {
          if(response) {
            if(response.status < 400) {
              cache.put(event.request, response.clone());
            }
            return Promise.resolve(response);
          } else {
            return Promise.reject('network request failed');
          }
        }),
      ], cache.match("/offline/index.html"));
    })
  );
});
```

Here, the code attempts to do two separate things.
It tries to simultaneously request a cache hit and resources from the network.
Again, we respond to the event with a collection of promises chained together to provide the functionality we want.

We open the cache again, just like before, and then pass two separate promises through a call to `promiseAny()`.
This is a function I (shamelessly) [stole](https://jakearchibald.com/2014/offline-cookbook/#cache-network-race) from the above linked article that returns a Promise.
This Promise resolves with the first resolved Promise, and rejects if both reject.

In this case, the two Promises passed into `promiseAny()` are calls to `fetch()` and `cache.match()`.
`fetch()` is from the new [Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API) exposed by javascript designed to replace the XMLHttpRequest syntax with one based around Promises.
The Promise returned from `fetch()` is transformed with `.then()` into another promise that checks if the response is not undefined, rejecting if it is, and then adds the response to the cache for future use with `cache.put()`.
This way, any requests are automatically added to the cache, allowing the page to respond incredibly fast in case the user navigates to a page visited before.

The other Promise, the call to `cache.match()`, is the killer.
Here, we check to see if the Request has been cached by the service worker.
If it has, immediately respond to the user with that data.
It might be stale, but being a blog, stuff doesn't change that much. 
I want to figure out a way to bypass the cache after a certain time period, but I'm working on it.
The other thing the cache Promise chain does is check if the response is not an error.
Caching a 404 error page is a bad idea, because now all the user will see when they navigate to that url (even if the page now exists) is a 404 error, until the cache is replaced.

The nice thing about this setup is that the network and the cache are racing to respond first.
If the disk is slow and the network is fast, the request to the internet will hit the user first.
If it's the other way around, the user will get a response from the cache.
Whichever happens, the user gets the fastest possible response.
Another benefit is that the cache is updated after every request.
No data is saved (another possibility with service workers) but time is reduced to be imperceptible if loading a cached resource.

You might have noticed the second argument to `promiseAny()`, which is a generic fallback.
This'll be expanded in the future to include fallbacks for different types of media, but right now it responds with a general 'offline' page in the case that the network is not responding and the cache has nothing.
It's nice to have this functionality so I can tell the user their exact situation instead of an obscure error about some Promise being rejected.

{{< a2 "Reducing processing" >}}

The biggest speed up is probably gained by using a static site instead of a server-side blogging platform.
The entire site is html, css, and some non-DOM-altering javascript, so it's very quick to paint once received.
There is no php processing to be done before sending the client the files, and no client-side processing to show them.

It actually feels a little nice to go back to web basics.
I'm working on a complicated Rust backend and Elm frontend website and while it's fun, it's complicated.
Elm is fairly new to me, and while I'm a little more experienced with Rust I've never designed and built a server backend before.
In addition, due to using an entirely javascript-based DOM, it's way more complicated from download to first paint than this webpage.

Anyways, this website is simply a few files.
Nothing to do before sending them to the user, so it's speedy quick.

{{< a2 Conclusions >}}

Making a speedy site isn't hard, but it includes some sacrifices.
No hero images or fancy pure functions to encode my virtual DOM.

I don't have the experience or expertise to denounce those trends, and I don't intend to.
Pupil's website has both.
However, it is nice to see what I can build simply with some html and css and google skills.
An exercise in minimalism.

Of course, there are many more things I can do to make this page faster.
I'm hosting this on Gitlab Pages, so I don't actually have control over the server caching rules or headers.
Some nginx reverse proxy would allow me to do more specialized stuff to increase speed, but that'll have to wait for another time.

All in all, it's been fun to make this site, and I've learned a lot.
