from pje_automation.utils.names import mask_cpf, sanitize_filename


def test_sanitize_filename_removes_invalid_characters() -> None:
    assert sanitize_filename('Nome:Teste<>*') == "Nome_Teste"


def test_mask_cpf_masks_middle_digits() -> None:
    assert mask_cpf("12345678901") == "123.***.***-01"
