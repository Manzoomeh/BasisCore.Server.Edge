// BasisCore Edge - Static File Server Demo JavaScript

console.log('✅ JavaScript file loaded successfully!');
console.log('Static file handler is working correctly.');

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    const testBtn = document.getElementById('testBtn');
    const result = document.getElementById('result');
    
    if (testBtn && result) {
        testBtn.addEventListener('click', function() {
            result.textContent = '🎉 JavaScript is working! Static files loaded successfully.';
            result.style.animation = 'fadeIn 0.5s ease-in';
            
            console.log('Button clicked! Static file serving is working perfectly.');
        });
    }
    
    // Log some useful information
    console.log('Current URL:', window.location.href);
    console.log('Page loaded at:', new Date().toLocaleString());
});

// Export a test function
window.testStaticHandler = function() {
    return {
        status: 'success',
        message: 'StaticFileHandler is working correctly!',
        timestamp: new Date().toISOString()
    };
};
