import os


def export_to_vtk(model, filename=None):
    '''
    Export the model to a vtk file

    Args:
        model: Femora Model instance with an assembled mesh.
        filename (str, optional): The filename to export to. If None,
                                uses model_name in model_path

    Returns:
        bool: True if export was successful, False otherwise
    '''
    if True:
        # Determine the full file path
        if filename is None:
            if model.model_name is None or model.model_path is None:
                raise ValueError("Either provide a filename or set model_name and model_path")
            filename = os.path.join(model.model_path, f"{model.model_name}.vtk")

        # check if the end is not .vtk then add it
        if not filename.endswith('.vtk'):
            filename += '.vtk'
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)

        # Get the assembled content
        if model.assembled_mesh is None:
            print("No mesh found")
            raise ValueError("No mesh found\n Please assemble the mesh first")

        # export to vtk
        # model.assembled_mesh.save(filename, binary=True)
        try:
            model.assembled_mesh.save(filename, binary=True)
        except Exception as e:
            raise e
    return True
