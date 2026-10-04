from app.db.models import Document, Person
from tests.conftest import login
from tests.synthetic import encode_jpeg, photograph, render_rg_back


def upload_rg(client):
    image = encode_jpeg(photograph(render_rg_back()))
    return client.post(
        "/documentos",
        data={"doc_type": "rg"},
        files={"front": ("frente.jpg", image, "image/jpeg"), "back": ("verso.jpg", image, "image/jpeg")},
        follow_redirects=False,
    )


def test_dashboard_renders_empty(client):
    login(client)
    response = client.get("/")
    assert response.status_code == 200
    assert "Nenhum documento ainda" in response.text


def test_full_flow_upload_review_and_delete(client):
    login(client)
    response = upload_rg(client)
    assert response.status_code == 303
    document_url = response.headers["location"]

    page = client.get(document_url)
    assert "MARIANA OLIVEIRA DOS SANTOS" in page.text
    assert "529.982.247-25" in page.text

    with client.app_state.session_factory() as session:
        document = session.query(Document).one()
        assert document.status == "pending_review"
        assert len(document.images) == 2
        image_id = document.images[0].id

    thumbnail = client.get(f"/imagens/{image_id}/miniatura")
    assert thumbnail.headers["content-type"] == "image/webp"
    original = client.get(f"/imagens/{image_id}/original")
    assert original.content[:2] == b"\xff\xd8"

    saved = client.post(
        document_url,
        data={
            "full_name": "MARIANA O. DOS SANTOS",
            "cpf": "529.982.247-25",
            "birth_date": "23/09/1991",
            "rg_number": "48.217.395-6",
        },
        follow_redirects=False,
    )
    assert saved.status_code == 303

    with client.app_state.session_factory() as session:
        document = session.query(Document).one()
        assert document.status == "reviewed"
        assert document.reviewed_manually
        person = session.query(Person).one()
        assert person.cpf == "52998224725"
        assert person.full_name == "MARIANA O. DOS SANTOS"

    upload_rg(client)
    with client.app_state.session_factory() as session:
        second = session.query(Document).order_by(Document.id.desc()).first()
        second_id = second.id
    client.post(f"/documentos/{second_id}", data={"cpf": "529.982.247-25", "full_name": "MARIANA OLIVEIRA DOS SANTOS"})
    with client.app_state.session_factory() as session:
        assert session.query(Person).count() == 1
        person_id = session.query(Person).one().id

    storage_dir = client.app_state.settings.storage_dir
    assert any(storage_dir.rglob("*.bin"))
    client.post(f"/pessoas/{person_id}/excluir")
    with client.app_state.session_factory() as session:
        assert session.query(Person).count() == 0
        assert session.query(Document).count() == 0
    assert not any(storage_dir.rglob("*.bin"))


def test_rejects_invalid_image(client):
    login(client)
    response = client.post(
        "/documentos",
        data={"doc_type": "rg"},
        files={"front": ("x.jpg", b"garbage", "image/jpeg")},
    )
    assert response.status_code == 400
    assert "imagem válida" in response.text


def test_reprocess_reruns_ocr_on_stored_original(client):
    login(client)
    document_url = upload_rg(client).headers["location"]
    client.post(document_url, data={"full_name": "NOME CORRIGIDO", "cpf": "529.982.247-25"})
    with client.app_state.session_factory() as session:
        assert session.query(Document).one().status == "reviewed"

    response = client.post(f"{document_url}/reprocessar", follow_redirects=False)
    assert response.status_code == 303

    with client.app_state.session_factory() as session:
        document = session.query(Document).one()
        assert document.status == "pending_review"
        assert document.full_name == "MARIANA OLIVEIRA DOS SANTOS"
        assert len(document.images) == 2
