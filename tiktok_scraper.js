function scrapeComments(callback) {
    var commentsDivXPath                 = '//div[contains(@class, "DivCommentListContainer")]';
    var allCommentsXPath                 = '//div[contains(@class, "DivCommentContentContainer")]';
    var level2CommentsXPath              = '//div[contains(@class, "DivReplyContainer")]';

    var publisherProfileUrlXPath         = '//span[contains(@class, "SpanUniqueId")]';
    var nicknameAndTimePublishedAgoXPath = '//span[contains(@class, "SpanOtherInfos")]';

    var likesCommentsSharesXPath         = "//strong[contains(@class, 'StrongText')]";

    var postUrlXPath                     = '//div[contains(@class, "CopyLinkText")]'
    var descriptionXPath                 = '//h4[contains(@class, "H4Link")]/preceding-sibling::div'

    var viewMoreDivXPath                 = '//p[contains(@class, "PReplyAction") and contains(., "View")]';

    function getElementsByXPath(xpath, parent) {
        let results = [];
        let query = document.evaluate(xpath, parent || document,
            null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
        for (let i = 0, length = query.snapshotLength; i < length; ++i) {
            results.push(query.snapshotItem(i));
        }
        return results;
    }

    function getAllComments() {
        return getElementsByXPath(allCommentsXPath);
    }

    function quoteString(s) {
        return '"' + String(s).replaceAll('"', '""') + '"';
    }

    function getNickname(comment) {
        return getElementsByXPath('./div[1]/a', comment)[0].outerText;
    }

    function isReply(comment) {
        return comment.parentElement.className.includes('Reply')
    }

    function formatDate(strDate) {
        if (typeof strDate !== 'undefined' && strDate !== null) {
            f = strDate.split('-');
            if (f.length == 1) {
                return strDate;
            } else if (f.length == 2) {
                return f[1] + '-' + f[0] + '-' + (new Date().getFullYear());
            } else if (f.length == 3) {
                return f[2] + '-' + f[1] + '-' + f[0];
            } else {
                return 'Malformed date';
            }
        } else {
            return 'No date';
        }
    }

    function extractNumericStats() {
        var strongTags = getElementsByXPath(likesCommentsSharesXPath);
        var likesCommentsShares = parseInt(strongTags[(strongTags.length - 3)].outerText) ? strongTags.slice(-3) : strongTags.slice(-2);
        return likesCommentsShares;
    }

    function csvFromComment(comment) {
        var nickname = getNickname(comment);
        var user = getElementsByXPath('./a', comment)[0]['href'].split('?')[0].split('/')[3].slice(1);
        var commentText = getElementsByXPath('./div[1]/p', comment)[0].outerText;
        var timeCommentedAgo = formatDate(getElementsByXPath('./div[1]/p[2]/span', comment)[0].outerText);
        var commentLikesCount = getElementsByXPath('./div[2]', comment)[0].outerText;
        var pic = getElementsByXPath('./a/span/img', comment)[0] ? getElementsByXPath('./a/span/img', comment)[0]['src'] : "N/A";
        return quoteString(nickname) + ',' + quoteString(user) + ',' + 'https://www.tiktok.com/@' + user + ','
             + quoteString(commentText) + ',' + timeCommentedAgo + ',' + commentLikesCount + ',' + quoteString(pic);
    }

    function loadFirstLevelComments(callback) {
        var loadingCommentsBuffer = 30;
        var numOfcommentsBeforeScroll = getAllComments().length;

        function scrollAndLoad() {
            if (loadingCommentsBuffer > 0) {
                var allComments = getAllComments();
                var lastComment = allComments[allComments.length - 1];
                
                var numOfcommentsAftScroll = getAllComments().length;

                if (numOfcommentsAftScroll !== numOfcommentsBeforeScroll) {
                    loadingCommentsBuffer = 15;
                } else {
                    var commentsDiv = getElementsByXPath(commentsDivXPath)[0];
                    commentsDiv.scrollIntoView(false);
                    loadingCommentsBuffer--;
                }
                numOfcommentsBeforeScroll = numOfcommentsAftScroll;
                console.log('Loading 1st level comment number ' + numOfcommentsAftScroll);

                setTimeout(scrollAndLoad, 300);
            } else {
                console.log('Opened all 1st level comments');
                callback();
            }
        }

        scrollAndLoad();
    }

    function loadSecondLevelComments(callback) {
        var loadingCommentsBuffer = 5;

        function clickAndLoad() {
            if (loadingCommentsBuffer > 0) {
                var readMoreDivs = getElementsByXPath(viewMoreDivXPath);
                for (var i = 0; i < readMoreDivs.length; i++) {
                    readMoreDivs[i].click();
                }

                if (readMoreDivs.length === 0) {
                    loadingCommentsBuffer--;
                } else {
                    loadingCommentsBuffer = 5;
                }
                console.log('Buffer ' + loadingCommentsBuffer);

                setTimeout(clickAndLoad, 500);
            } else {
                console.log('Opened all 2nd level comments');
                callback();
            }
        }

        clickAndLoad();
    }

    loadFirstLevelComments(function() {
        loadSecondLevelComments(function() {
            // Reading all comments, extracting and converting the data to csv
            var comments = getAllComments();
            var level2CommentsLength = getElementsByXPath(level2CommentsXPath).length;
            var publisherProfileUrl = getElementsByXPath(publisherProfileUrlXPath)[0].outerText;
            var nicknameAndTimePublishedAgo = getElementsByXPath(nicknameAndTimePublishedAgoXPath)[0].outerText.replaceAll('\n', ' ').split(' · ');

            var url = window.location.href.split('?')[0]
            var likesCommentsShares = extractNumericStats();
            var likes = likesCommentsShares[0].outerText;
            var totalComments = likesCommentsShares[1].outerText;

            var shares = likesCommentsShares[2] ? likesCommentsShares[2].outerText : "N/A";
            var commentNumberDifference = Math.abs(parseInt(totalComments) - (comments.length));

            var csv = 'Now,' + new Date().toString() + '\n';
            csv += 'Post URL,' + url + '\n';
            csv += 'Publisher Nickname,' + nicknameAndTimePublishedAgo[0] + '\n';
            csv += 'Publisher @,' + publisherProfileUrl + '\n';
            csv += 'Publisher URL,' + "https://www.tiktok.com/@" + publisherProfileUrl + '\n';
            csv += 'Publish Time,' + formatDate(nicknameAndTimePublishedAgo[1]) + '\n';
            csv += 'Post Likes,' + likes + '\n';
            csv += 'Post Shares,' + shares + '\n';
            csv += 'Description,' + quoteString(getElementsByXPath(descriptionXPath)[0].outerText) + '\n';
            csv += 'Number of 1st level comments,' + (comments.length - level2CommentsLength) + '\n';
            csv += 'Number of 2nd level comments,' + level2CommentsLength + '\n';
            csv += '"Total Comments (actual, in this list, rendered in the comment section; needs all comments to be loaded!)",' + (comments.length) + '\n';
            csv += "Total Comments (which TikTok tells you; it's too high most of the time when dealing with many comments OR way too low because TikTok limits the number of comments to prevent scraping)," + totalComments + '\n';
            csv += "Difference," + commentNumberDifference + '\n';
            csv += 'Comment Number (ID),Nickname,User @,User URL,Comment Text,Time,Likes,Profile Picture URL,Is 2nd Level Comment,User Replied To,Number of Replies\n';

            var count = 1;
            var totalReplies = 0;
            var repliesSeen = 1;
            for (var i = 0; i < comments.length; i++) {
                csv += count + ',' + csvFromComment(comments[i]) + ',';
                if (i > 0 && isReply(comments[i])) {
                    csv += "Yes," + quoteString(getNickname(comments[i - repliesSeen])) + ',0';
                    repliesSeen += 1;
                }
                else {
                    csv += 'No,---,';
                    totalReplies = 0;
                    repliesSeen = 1;
                    for (var j = 1; j < comments.length - i; j++) {
                        if (!isReply(comments[i + j])) {
                            break;
                        }
                        totalReplies += 1;
                    }
                    csv += totalReplies;
                }
                csv += '\n';
                count++;
            }
            var apparentCommentNumber = parseInt(totalComments);
            console.log('Number of magically missing comments (not rendered in the comment section): ' + (apparentCommentNumber - count + 1) + ' (you have ' + (count - 1) + ' of ' + apparentCommentNumber + ')');
            console.log('CSV data ready');

            callback(JSON.stringify({ csv: csv }));
        });
    });
}

// This part will be executed by Selenium
scrapeComments(function(result) {
    // Store the result in a global variable that Selenium can access
    window.scrapedData = result;
});

// Return a placeholder value
"Scraping in progress"
