from flask import abort, g, request
from .country_service import get_country, MEMBER_GROUPS, destination
from .project_service import project_for, products_for

def workspace_context(country):
    context={"country":get_country(country),"project":None,"products":[],"selected_product":None}
    pid=request.args.get("project_id")
    if pid:
        if not g.user:
            abort(401)
        project=project_for(g.user["id"],pid)
        if project["country"]!=country:
            abort(404)
        products=products_for(g.user["id"],pid)
        selected=request.args.get("product_id")
        product=next((p for p in products if p["id"]==selected),None)
        if selected and product is None:
            abort(404)
        context.update(project=project,products=products,selected_product=product or (products[0] if products else None))
    member=(context["project"]["member_state"] if context["project"] else request.args.get("member_state", "")) or ""
    target=destination(country,member)
    context.update(member_state=member,destination=target,member_options=MEMBER_GROUPS.get(country,{}))
    g.destination_member=member
    return context
