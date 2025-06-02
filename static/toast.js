window.addEventListener('DOMContentLoaded', function() {
    var toast = document.getElementById('toast');
    var msg = document.getElementById('toast-message');
    var messages = toast.getAttribute('data-messages');
    if (messages && messages !== 'null' && messages !== '[]') {
        try {
            messages = JSON.parse(messages);
        } catch {
            messages = [];
        }
        // Tampilkan semua pesan satu per satu
        let i = 0;
        function showNextToast() {
            if (i >= messages.length) return;
            msg.textContent = messages[i][1];
            toast.style.display = 'block';
            toast.style.opacity = 1;
            setTimeout(function() {
                toast.style.opacity = 0;
                setTimeout(function(){
                    toast.style.display = 'none';
                    i++;
                    showNextToast();
                }, 400);
            }, 2500);
        }
        showNextToast();
    }
});