function scrollToBottom() {
    const chatlist = document.getElementById('chatlist');
    if (chatlist) {
        chatlist.scrollTop = chatlist.scrollHeight;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const chatlist = document.getElementById('chatlist');
    if (chatlist) {
        // Initial scroll
        scrollToBottom();

        // Set up MutationObserver
        const observer = new MutationObserver(scrollToBottom);
        observer.observe(chatlist, { childList: true, subtree: true });

        // Listen for HTMX events
        document.body.addEventListener('htmx:afterOnLoad', scrollToBottom);
        document.body.addEventListener('htmx:wsAfterMessage', scrollToBottom);
    }
});

// Expose the function for global use
window.scrollToBottom = scrollToBottom;