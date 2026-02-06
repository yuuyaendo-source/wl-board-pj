module.exports = {
    apps: [{
        name: 'wl-sticky-note',
        script: 'server.js',
        instances: 1,
        exec_mode: 'fork',
        env: {
            NODE_ENV: 'development',
            PORT: 3000
        },
        env_production: {
            NODE_ENV: 'production',
            PORT: 3000
        },
        error_file: './logs/err.log',
        out_file: './logs/out.log',
        log_file: './logs/combined.log',
        time: true,
        autorestart: true,
        max_restarts: 10,
        min_uptime: '10s'
    }]
};
