{% load app_filters %}
function reportContent(uuid){
    var result = window.prompt('{{ 'What is the issue with this content you would like to report?'|etrans }}');
    if(result && result.length > 15) {
        var fd = {'uid': uuid, 'text': result};
        {% if request.GET.lang %}
        var extra = '?lang={{ request.GET.lang }}';
        {% else %}
        var extra = '';
        {% endif %}
        $.ajax({
            url: 'https://lotteh.com/feed/report/' + uuid + '/' + extra,
            method: 'POST',
            data: fd,
            tryCount: 0,
            retryLimit: 5,
            error: (xhr, textStatus, errorThrown) => {
                this.tryCount++;
                if(this.tryCount >= this.retryLimit) return;
                $.ajax(this);
            },
            success: function(data) {
                alert(data);
            }
        });
    }
}
