# SPDX-License-Identifier: GPL-3.0-or-later
install(FILES __init__.py cu8_a_c64.py rotador_frecuencia.py
        DESTINATION "${CBS33M_PYTHON_DIR}")

if(BUILD_TESTING)
    add_test(NAME cbs33m_python
             COMMAND "${Python3_EXECUTABLE}" -B "${CMAKE_CURRENT_SOURCE_DIR}/qa_cbs33m.py")
endif()
