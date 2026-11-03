function errorHandler(err, req, res, next) {

    console.error("Backend error:", err.message);

    res.status(500).json({
        status: "failed",
        message: "Backend request failed.",
        error: err.message
    });
}

module.exports = errorHandler;