def from_ml(val, unit):

    if unit == "l":
        val = val / 1000
    elif unit == "gal":
        val = val * 0.0002641721
    elif unit == "gal (imperial)":
        val = val * 0.000219969
    elif unit == "pt":
        val = val * 0.0021133764
    elif unit == "p (imperial)":
        val = val * 0.00175975
    elif unit == "qt":
        val = val * 0.0010566882
    elif unit == "qt (imperial)":
        val = val * 0.000879877
    elif unit == "cup":
        val = val * 0.0042267528
    elif unit == "cup (imperial)":
        val = val * 0.00351951
    elif unit == "oz":
        val = val * 0.033814
    elif unit == "oz (imperial)":
        val = val * 0.0351951
    else:
        raise Exception(f"invalid volume unit for conversion: {unit}'")
    return val