// Inject the button into the TikTok page
const scrapeAndAnalyzeButton = document.createElement('button');
scrapeAndAnalyzeButton.innerText = "Scrape and Analyze Comments";
scrapeAndAnalyzeButton.style.position = 'fixed';
scrapeAndAnalyzeButton.style.top = '10px';
scrapeAndAnalyzeButton.style.right = '10px';
scrapeAndAnalyzeButton.style.zIndex = '9999';
scrapeAndAnalyzeButton.style.padding = '10px';
scrapeAndAnalyzeButton.style.backgroundColor = '#4CAF50';
scrapeAndAnalyzeButton.style.color = '#FFF';
document.body.appendChild(scrapeAndAnalyzeButton);

// XPath definitions and utility functions
var commentsDivXPath = '//div[contains(@class, "DivCommentListContainer")]';
var allCommentsXPath = '//div[contains(@class, "DivCommentContentContainer")]';
var level2CommentsXPath = '//div[contains(@class, "DivReplyContainer")]';
var publisherProfileUrlXPath = '//span[contains(@class, "SpanUniqueId")]';
var nicknameAndTimePublishedAgoXPath = '//span[contains(@class, "SpanOtherInfos")]';
var likesCommentsSharesXPath = "//strong[contains(@class, 'StrongText')]";
var postUrlXPath = '//div[contains(@class, "CopyLinkText")]';
var descriptionXPath = '//h4[contains(@class, "H4Link")]/preceding-sibling::div';
var viewMoreDivXPath = '//p[contains(@class, "PReplyAction") and contains(., "View")]';

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
    return comment.parentElement.className.includes('Reply');
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
    nickname = getNickname(comment);
    user = getElementsByXPath('./a', comment)[0]['href'].split('?')[0].split('/')[3].slice(1);
    commentText = getElementsByXPath('./div[1]/p', comment)[0].outerText;
    timeCommentedAgo = formatDate(getElementsByXPath('./div[1]/p[2]/span', comment)[0].outerText);
    commentLikesCount = getElementsByXPath('./div[2]', comment)[0].outerText;
    pic = getElementsByXPath('./a/span/img', comment)[0] ? getElementsByXPath('./a/span/img', comment)[0]['src'] : "N/A";
    return quoteString(nickname) + ',' + quoteString(user) + ',' + 'https://www.tiktok.com/@' + user + ','
         + quoteString(commentText) + ',' + timeCommentedAgo + ',' + commentLikesCount + ',' + quoteString(pic);
}

// Updated scraping function to only scrape first-level comments
async function scrapeComments() {
    // Loading 1st level comments
    var loadingCommentsBuffer = 30;
    var numOfcommentsBeforeScroll = getAllComments().length;
    while (loadingCommentsBuffer > 0) {
        allComments = getAllComments();
        lastComment = allComments[allComments.length - 1];
        lastComment.scrollIntoView(false);

        numOfcommentsAftScroll = getAllComments().length;

        if (numOfcommentsAftScroll !== numOfcommentsBeforeScroll) {
            loadingCommentsBuffer = 15;
        } else {
            commentsDiv = getElementsByXPath(commentsDivXPath)[0];
            commentsDiv.scrollIntoView(false);
            loadingCommentsBuffer--;
        }
        numOfcommentsBeforeScroll = numOfcommentsAftScroll;
        console.log('Loading 1st level comment number ' + numOfcommentsAftScroll);

        await new Promise(r => setTimeout(r, 300));
    }
    console.log('Opened all 1st level comments');

    // Reading all first-level comments, extracting and converting the data to csv
    var comments = getAllComments();
    var publisherProfileUrl = getElementsByXPath(publisherProfileUrlXPath)[0].outerText;
    var nicknameAndTimePublishedAgo = getElementsByXPath(nicknameAndTimePublishedAgoXPath)[0].outerText.replaceAll('\n', ' ').split(' · ');

    var url = window.location.href.split('?')[0];
    var likesCommentsShares = extractNumericStats();
    var likes = likesCommentsShares[0].outerText;
    var totalComments = likesCommentsShares[1].outerText;

    var shares = likesCommentsShares[2] ? likesCommentsShares[2].outerText : "N/A";

    var csv = 'Now,' + Date() + '\n';
    csv += 'Post URL,' + url + '\n';
    csv += 'Publisher Nickname,' + nicknameAndTimePublishedAgo[0] + '\n';
    csv += 'Publisher @,' + publisherProfileUrl + '\n';
    csv += 'Publisher URL,' + "https://www.tiktok.com/@" + publisherProfileUrl + '\n';
    csv += 'Publish Time,' + formatDate(nicknameAndTimePublishedAgo[1]) + '\n';
    csv += 'Post Likes,' + likes + '\n';
    csv += 'Post Shares,' + shares + '\n';
    csv += 'Description,' + quoteString(getElementsByXPath(descriptionXPath)[0].outerText) + '\n';
    csv += 'Number of 1st level comments,' + comments.length + '\n';
    csv += "Total Comments (which TikTok tells you)," + totalComments + '\n';
    csv += 'Comment Number (ID),Nickname,User @,User URL,Comment Text,Time,Likes,Profile Picture URL\n';

    var count = 1;
    for (var i = 0; i < comments.length; i++) {
        csv += count + ',' + csvFromComment(comments[i]) + '\n';
        count++;
    }

    const parsedComments = csv.split('\n').slice(11).map(line => {
        const [id, nickname, user, userUrl, commentText, time, likes, profilePicUrl] = line.split(',');
        return {
            Nickname: nickname,
            "User @": user,
            "User URL": userUrl,
            "Comment_Text": commentText,
            Time: time,
            Likes: likes,
            "Profile Picture URL": profilePicUrl
        };
    });

    return {
        metadata: {
            "Post URL": url,
            "Publisher Nickname": nicknameAndTimePublishedAgo[0],
            "Publisher @": publisherProfileUrl,
            "Publisher URL": "https://www.tiktok.com/@" + publisherProfileUrl,
            "Publish Time": formatDate(nicknameAndTimePublishedAgo[1]),
            "Post Likes": likes,
            "Post Shares": shares,
            "Description": getElementsByXPath(descriptionXPath)[0].outerText,
            "Total Comments": totalComments
        },
        comments: parsedComments
    };
}

scrapeAndAnalyzeButton.addEventListener('click', async function () {
    const scrapedData = await scrapeComments();
    
    chrome.runtime.sendMessage({ 
        action: "analyzeComments", 
        comments: scrapedData.comments,
        metadata: scrapedData.metadata
    });
});

// Listen for messages from the popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "analyzeComments") {
        scrapeAndAnalyzeButton.click();
    }
});
