/* Existing page controls, kept outside templates. Bootstrap handles navigation. */
const uploadType = document.getElementById('content_type');
if (uploadType) {
    const songFields = document.getElementById('song_fields');
    const postFields = document.getElementById('post_fields');
    const updateUploadFields = () => {
        const isSong = uploadType.value === 'song';
        songFields.hidden = !isSong;
        postFields.hidden = isSong;
    };
    uploadType.addEventListener('change', updateUploadFields);
    updateUploadFields();
}
const trendingFilter = document.getElementById('trending-filter');
if (trendingFilter) {
    trendingFilter.addEventListener('change', () => {
        document.querySelectorAll('.trending-item').forEach(item => {
            item.hidden = trendingFilter.value !== 'all' && item.dataset.type !== trendingFilter.value;
        });
    });
}
