
if (Function.prototype.scope === undefined) {
    Function.prototype.scope = function(scope) {
        var _function = this;

        return function() {
            return _function.apply(scope, arguments);
        };
    };
}
