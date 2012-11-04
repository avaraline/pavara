def load_model(path):
    """
    Wrapper around direct.showbase.Loader.loadModel, for now. May handle remote asset loading in the future.
    """
    return loader.loadModel(path)
