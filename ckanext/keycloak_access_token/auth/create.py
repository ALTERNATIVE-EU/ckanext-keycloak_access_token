def access_token_create(context, data_dict):
    """Create new token for current user."""
    user = context["model"].User.get(data_dict["user"])
    return {"success": user.name == context["user"]}
