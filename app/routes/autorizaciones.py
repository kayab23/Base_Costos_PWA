from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from .. import schemas, db
from ..auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/autorizaciones", tags=["autorizaciones"])


def determinar_autorizador(precio_propuesto: float, sku: str, transporte: str, nivel_solicitante: str, conn):
    """
    Determina qué nivel debe autorizar basado en el precio propuesto y el nivel del solicitante.
    Nueva jerarquía de 4 niveles:
    - Vendedor → puede vender hasta precio_vendedor_min (necesita autorización si baja más)
    - Gerente_Comercial → puede autorizar hasta precio_gerente_com_min
    - Subdirección → puede autorizar hasta precio_subdireccion_min
    - Dirección → puede autorizar hasta precio_direccion_min
    """
    cursor = conn.cursor()
    
    # Obtener precios del producto
    cursor.execute("""
        SELECT precio_base_mxn, precio_vendedor_min, precio_gerente_com_min, 
               precio_subdireccion_min, precio_direccion_min
        FROM PreciosCalculados
        WHERE sku = ? AND transporte = ?
    """, (sku, transporte))
    
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    precio_base, precio_vendedor_min, precio_gerente_com_min, precio_subdireccion_min, precio_direccion_min = row
    
    # Convertir Decimals a float para cálculos
    precio_base = float(precio_base) if precio_base else 0
    precio_vendedor_min = float(precio_vendedor_min) if precio_vendedor_min else 0
    precio_gerente_com_min = float(precio_gerente_com_min) if precio_gerente_com_min else 0
    precio_subdireccion_min = float(precio_subdireccion_min) if precio_subdireccion_min else 0
    precio_direccion_min = float(precio_direccion_min) if precio_direccion_min else 0
    
    # Validar que no sea menor al precio base (Mark-up)
    if precio_propuesto < precio_base:
        raise HTTPException(
            status_code=400, 
            detail=f"El precio propuesto (${precio_propuesto:,.2f}) no puede ser menor al precio base (${precio_base:,.2f})"
        )
    
    # Determinar nivel autorizador según el nivel del solicitante
    # Lógica simple: si el precio está por debajo del mínimo del solicitante,
    # va al siguiente nivel jerárquico, sin importar qué tan bajo sea
    
    if nivel_solicitante == 'Vendedor':
        # Si el precio propuesto está por debajo de su mínimo, va a Gerencia_Comercial
        if precio_propuesto < precio_vendedor_min:
            return 'Gerencia_Comercial', precio_vendedor_min
        else:
            raise HTTPException(
                status_code=400,
                detail=f"El precio propuesto (${precio_propuesto:,.2f}) está dentro de tu rango autorizado (≥${precio_vendedor_min:,.2f}). No necesitas autorización."
            )
    
    elif nivel_solicitante == 'Gerencia_Comercial':
        # Si el precio propuesto está por debajo de su mínimo, va a Subdirección
        if precio_propuesto < precio_gerente_com_min:
            return 'Subdireccion', precio_gerente_com_min
        else:
            raise HTTPException(
                status_code=400,
                detail=f"El precio propuesto (${precio_propuesto:,.2f}) está dentro de tu rango autorizado (≥${precio_gerente_com_min:,.2f}). No necesitas autorización."
            )
    
    elif nivel_solicitante == 'Subdireccion':
        # Si el precio propuesto está por debajo de su mínimo, va a Dirección
        if precio_propuesto < precio_subdireccion_min:
            return 'Direccion', precio_subdireccion_min
        else:
            raise HTTPException(
                status_code=400,
                detail=f"El precio propuesto (${precio_propuesto:,.2f}) está dentro de tu rango autorizado (≥${precio_subdireccion_min:,.2f}). No necesitas autorización."
            )
    
    else:
        raise HTTPException(status_code=400, detail="Este nivel no puede solicitar autorizaciones")


@router.post("/solicitar", response_model=schemas.SolicitudAutorizacion)
def crear_solicitud(
    solicitud: schemas.SolicitudAutorizacionCreate,
    current_user: schemas.UserInfo = Depends(get_current_user),
    conn = Depends(db.get_connection)
):
    """Crear una solicitud de autorización de descuento"""
    
    # Validar que el usuario tenga un rol que pueda solicitar autorizaciones
    if current_user["rol"] not in ['Vendedor', 'Gerencia_Comercial', 'Subdireccion']:
        raise HTTPException(status_code=403, detail="Solo Vendedores, Gerencia Comercial y Subdirección pueden solicitar autorizaciones")
    
    # Determinar nivel autorizador y precio mínimo actual
    nivel_autorizador, precio_minimo_actual = determinar_autorizador(
        solicitud.precio_propuesto,
        solicitud.sku,
        solicitud.transporte,
        current_user["rol"],
        conn
    )
    
    # Calcular descuento adicional
    descuento_adicional_pct = ((float(precio_minimo_actual) - solicitud.precio_propuesto) / float(precio_minimo_actual)) * 100
    
    # Insertar solicitud
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO SolicitudesAutorizacion 
        (sku, transporte, solicitante_id, nivel_solicitante, precio_propuesto, 
         precio_minimo_actual, descuento_adicional_pct, cliente, cantidad, justificacion, 
         estado, fecha_solicitud)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pendiente', GETDATE())
    """, (
        solicitud.sku,
        solicitud.transporte,
        current_user["usuario_id"],
        current_user["rol"],
        solicitud.precio_propuesto,
        precio_minimo_actual,
        descuento_adicional_pct,
        solicitud.cliente,
        solicitud.cantidad,
        solicitud.justificacion
    ))
    
    # Obtener ID de la solicitud creada
    cursor.execute("SELECT @@IDENTITY")
    solicitud_id = cursor.fetchone()[0]
    
    conn.commit()
    
    # Retornar la solicitud creada
    cursor.execute("""
        SELECT id, sku, transporte, solicitante_id, solicitante, nivel_solicitante,
               precio_propuesto, precio_minimo_actual, descuento_adicional_pct,
               cliente, cantidad, justificacion, estado, autorizador_id, autorizador,
               fecha_solicitud, fecha_respuesta, comentarios_autorizador
        FROM vw_SolicitudesAutorizacion
        WHERE id = ?
    """, (solicitud_id,))
    
    row = cursor.fetchone()
    return schemas.SolicitudAutorizacion(
        id=row[0],
        sku=row[1],
        transporte=row[2],
        solicitante_id=row[3],
        solicitante=row[4],
        nivel_solicitante=row[5],
        precio_propuesto=row[6],
        precio_minimo_actual=row[7],
        descuento_adicional_pct=row[8],
        cliente=row[9],
        cantidad=row[10],
        justificacion=row[11],
        estado=row[12],
        autorizador_id=row[13],
        autorizador=row[14],
        fecha_solicitud=row[15],
        fecha_respuesta=row[16],
        comentarios_autorizador=row[17]
    )


@router.get("/mis-solicitudes", response_model=List[schemas.SolicitudAutorizacion])
def obtener_mis_solicitudes(
    current_user: schemas.UserInfo = Depends(get_current_user),
    conn = Depends(db.get_connection)
):
    """Obtener las solicitudes del usuario actual"""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, sku, transporte, solicitante_id, solicitante, nivel_solicitante,
               precio_propuesto, precio_minimo_actual, descuento_adicional_pct,
               cliente, cantidad, justificacion, estado, autorizador_id, autorizador,
               fecha_solicitud, fecha_respuesta, comentarios_autorizador
        FROM vw_SolicitudesAutorizacion
        WHERE solicitante_id = ?
        ORDER BY fecha_solicitud DESC
    """, (current_user["usuario_id"],))
    
    solicitudes = []
    for row in cursor.fetchall():
        solicitudes.append(schemas.SolicitudAutorizacion(
            id=row[0],
            sku=row[1],
            transporte=row[2],
            solicitante_id=row[3],
            solicitante=row[4],
            nivel_solicitante=row[5],
            precio_propuesto=row[6],
            precio_minimo_actual=row[7],
            descuento_adicional_pct=row[8],
            cliente=row[9],
            cantidad=row[10],
            justificacion=row[11],
            estado=row[12],
            autorizador_id=row[13],
            autorizador=row[14],
            fecha_solicitud=row[15],
            fecha_respuesta=row[16],
            comentarios_autorizador=row[17]
        ))
    
    return solicitudes


@router.get("/procesadas", response_model=List[schemas.SolicitudAutorizacion])
def obtener_solicitudes_procesadas(
    current_user: schemas.UserInfo = Depends(get_current_user),
    conn = Depends(db.get_connection)
):
    """Obtener solicitudes que el usuario ha aprobado o rechazado"""
    
    # Solo Gerencia Comercial, Subdirección, Dirección y admin pueden ver su historial
    if current_user["rol"] not in ['Gerencia_Comercial', 'Subdireccion', 'Direccion', 'admin']:
        raise HTTPException(status_code=403, detail="No tiene permisos para ver historial de aprobaciones")
    
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, sku, transporte, solicitante_id, solicitante, nivel_solicitante,
               precio_propuesto, precio_minimo_actual, descuento_adicional_pct,
               cliente, cantidad, justificacion, estado, autorizador_id, autorizador,
               fecha_solicitud, fecha_respuesta, comentarios_autorizador
        FROM vw_SolicitudesAutorizacion
        WHERE autorizador_id = ? AND estado IN ('Aprobada', 'Rechazada')
        ORDER BY fecha_respuesta DESC
    """, (current_user["usuario_id"],))
    
    solicitudes = []
    for row in cursor.fetchall():
        solicitudes.append(schemas.SolicitudAutorizacion(
            id=row[0],
            sku=row[1],
            transporte=row[2],
            solicitante_id=row[3],
            solicitante=row[4],
            nivel_solicitante=row[5],
            precio_propuesto=row[6],
            precio_minimo_actual=row[7],
            descuento_adicional_pct=row[8],
            cliente=row[9],
            cantidad=row[10],
            justificacion=row[11],
            estado=row[12],
            autorizador_id=row[13],
            autorizador=row[14],
            fecha_solicitud=row[15],
            fecha_respuesta=row[16],
            comentarios_autorizador=row[17]
        ))
    
    return solicitudes


@router.get("/pendientes", response_model=List[schemas.SolicitudAutorizacion])
def obtener_solicitudes_pendientes(
    current_user: schemas.UserInfo = Depends(get_current_user),
    conn = Depends(db.get_connection)
):
    """Obtener solicitudes pendientes que el usuario puede autorizar"""
    
    # Solo roles autorizadores pueden ver solicitudes pendientes
    if current_user["rol"] not in ['Gerencia_Comercial', 'Subdireccion', 'Direccion', 'admin']:
        raise HTTPException(status_code=403, detail="No tiene permisos para ver solicitudes pendientes")
    
    cursor = conn.cursor()
    
    # Cada nivel ve solo las solicitudes que puede autorizar
    if current_user["rol"] == 'Gerencia_Comercial':
        cursor.execute("""
            SELECT s.id, s.sku, s.transporte, s.solicitante_id, s.solicitante, s.nivel_solicitante,
                   s.precio_propuesto, s.precio_minimo_actual, s.descuento_adicional_pct,
                   s.cliente, s.cantidad, s.justificacion, s.estado, s.autorizador_id, s.autorizador,
                   s.fecha_solicitud, s.fecha_respuesta, s.comentarios_autorizador
            FROM vw_SolicitudesAutorizacion s
            INNER JOIN PreciosCalculados p ON s.sku = p.sku AND s.transporte = p.transporte
            WHERE s.estado = 'Pendiente' 
            AND s.nivel_solicitante = 'Vendedor'
            AND s.precio_propuesto >= p.precio_gerente_com_min
            ORDER BY s.fecha_solicitud
        """)
    elif current_user["rol"] == 'Subdireccion':
        cursor.execute("""
            SELECT s.id, s.sku, s.transporte, s.solicitante_id, s.solicitante, s.nivel_solicitante,
                   s.precio_propuesto, s.precio_minimo_actual, s.descuento_adicional_pct,
                   s.cliente, s.cantidad, s.justificacion, s.estado, s.autorizador_id, s.autorizador,
                   s.fecha_solicitud, s.fecha_respuesta, s.comentarios_autorizador
            FROM vw_SolicitudesAutorizacion s
            INNER JOIN PreciosCalculados p ON s.sku = p.sku AND s.transporte = p.transporte
            WHERE s.estado = 'Pendiente' 
            AND s.nivel_solicitante IN ('Vendedor', 'Gerencia_Comercial')
            AND s.precio_propuesto >= p.precio_subdireccion_min
            ORDER BY s.fecha_solicitud
        """)
    else:  # Dirección o admin
        cursor.execute("""
            SELECT id, sku, transporte, solicitante_id, solicitante, nivel_solicitante,
                   precio_propuesto, precio_minimo_actual, descuento_adicional_pct,
                   cliente, cantidad, justificacion, estado, autorizador_id, autorizador,
                   fecha_solicitud, fecha_respuesta, comentarios_autorizador
            FROM vw_SolicitudesAutorizacion
            WHERE estado = 'Pendiente'
            ORDER BY fecha_solicitud
        """)
    
    solicitudes = []
    for row in cursor.fetchall():
        solicitudes.append(schemas.SolicitudAutorizacion(
            id=row[0],
            sku=row[1],
            transporte=row[2],
            solicitante_id=row[3],
            solicitante=row[4],
            nivel_solicitante=row[5],
            precio_propuesto=row[6],
            precio_minimo_actual=row[7],
            descuento_adicional_pct=row[8],
            cliente=row[9],
            cantidad=row[10],
            justificacion=row[11],
            estado=row[12],
            autorizador_id=row[13],
            autorizador=row[14],
            fecha_solicitud=row[15],
            fecha_respuesta=row[16],
            comentarios_autorizador=row[17]
        ))
    
    return solicitudes


@router.put("/{solicitud_id}/aprobar", response_model=schemas.SolicitudAutorizacion)
def aprobar_solicitud(
    solicitud_id: int,
    respuesta: schemas.SolicitudAutorizacionResponse,
    current_user: schemas.UserInfo = Depends(get_current_user),
    conn = Depends(db.get_connection)
):
    """Aprobar una solicitud de autorización"""
    
    if current_user["rol"] not in ['Gerencia_Comercial', 'Gerencia', 'admin']:
        raise HTTPException(status_code=403, detail="No tiene permisos para aprobar solicitudes")
    
    cursor = conn.cursor()
    
    # Verificar que la solicitud existe y está pendiente
    cursor.execute("""
        SELECT s.*, p.precio_gerencia_com_min
        FROM SolicitudesAutorizacion s
        INNER JOIN PreciosCalculados p ON s.sku = p.sku AND s.transporte = p.transporte
        WHERE s.id = ?
    """, (solicitud_id,))
    
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    if row[11] != 'Pendiente':  # estado (índice 11 = columna 12)
        raise HTTPException(status_code=400, detail="La solicitud ya fue procesada")
    
    # Validar que el usuario tiene nivel suficiente para aprobar
    nivel_solicitante = row[4]  # nivel_solicitante (índice 4 = columna 5)
    precio_propuesto = row[5]  # precio_propuesto (índice 5 = columna 6)
    precio_gerencia_com_min = row[16]  # de la JOIN (índice 16 = columna 17: última columna)
    
    # Jerarquía de aprobación:
    # - Gerencia_Comercial puede aprobar solicitudes de Vendedor con precio >= precio_gerencia_com_min
    # - Gerencia puede aprobar solicitudes de Vendedor (cualquier precio) y de Gerencia_Comercial
    # - admin puede aprobar cualquier solicitud
    
    if current_user["rol"] == 'Gerencia_Comercial':
        # Solo puede aprobar solicitudes de Vendedor con precio en su rango
        if nivel_solicitante != 'Vendedor':
            raise HTTPException(
                status_code=403,
                detail="Gerencia Comercial solo puede aprobar solicitudes de Vendedores"
            )
        if precio_propuesto < precio_gerencia_com_min:
            raise HTTPException(
                status_code=403,
                detail="El precio propuesto está por debajo de su nivel de autorización. Debe ser aprobado por Gerencia"
            )
    elif current_user["rol"] == 'Gerencia':
        # Puede aprobar solicitudes de Vendedor y Gerencia_Comercial
        if nivel_solicitante not in ['Vendedor', 'Gerencia_Comercial']:
            raise HTTPException(
                status_code=403,
                detail="No tiene autoridad para aprobar esta solicitud"
            )
    # admin puede aprobar cualquier solicitud (no hay restricción)
    
    # Aprobar solicitud
    cursor.execute("""
        UPDATE SolicitudesAutorizacion
        SET estado = 'Aprobada',
            autorizador_id = ?,
            fecha_respuesta = GETDATE(),
            comentarios_autorizador = ?
        WHERE id = ?
    """, (current_user["usuario_id"], respuesta.comentarios, solicitud_id))
    
    conn.commit()
    
    # Retornar solicitud actualizada
    cursor.execute("""
        SELECT id, sku, transporte, solicitante_id, solicitante, nivel_solicitante,
               precio_propuesto, precio_minimo_actual, descuento_adicional_pct,
               cliente, cantidad, justificacion, estado, autorizador_id, autorizador,
               fecha_solicitud, fecha_respuesta, comentarios_autorizador
        FROM vw_SolicitudesAutorizacion
        WHERE id = ?
    """, (solicitud_id,))
    
    row = cursor.fetchone()
    return schemas.SolicitudAutorizacion(
        id=row[0],
        sku=row[1],
        transporte=row[2],
        solicitante_id=row[3],
        solicitante=row[4],
        nivel_solicitante=row[5],
        precio_propuesto=row[6],
        precio_minimo_actual=row[7],
        descuento_adicional_pct=row[8],
        cliente=row[9],
        cantidad=row[10],
        justificacion=row[11],
        estado=row[12],
        autorizador_id=row[13],
        autorizador=row[14],
        fecha_solicitud=row[15],
        fecha_respuesta=row[16],
        comentarios_autorizador=row[17]
    )


@router.put("/{solicitud_id}/rechazar", response_model=schemas.SolicitudAutorizacion)
def rechazar_solicitud(
    solicitud_id: int,
    respuesta: schemas.SolicitudAutorizacionResponse,
    current_user: schemas.UserInfo = Depends(get_current_user),
    conn = Depends(db.get_connection)
):
    """Rechazar una solicitud de autorización"""
    
    if current_user["rol"] not in ['Gerencia_Comercial', 'Gerencia', 'admin']:
        raise HTTPException(status_code=403, detail="No tiene permisos para rechazar solicitudes")
    
    cursor = conn.cursor()
    
    # Verificar que la solicitud existe y está pendiente
    cursor.execute("""
        SELECT s.estado, s.nivel_solicitante, s.precio_propuesto, p.precio_gerencia_com_min
        FROM SolicitudesAutorizacion s
        INNER JOIN PreciosCalculados p ON s.sku = p.sku AND s.transporte = p.transporte
        WHERE s.id = ?
    """, (solicitud_id,))
    row = cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    if row[0] != 'Pendiente':
        raise HTTPException(status_code=400, detail="La solicitud ya fue procesada")
    
    # Validar que el usuario tiene nivel suficiente para rechazar
    # (misma jerarquía que para aprobar)
    nivel_solicitante = row[1]
    precio_propuesto = row[2]
    precio_gerencia_com_min = row[3]
    
    if current_user["rol"] == 'Gerencia_Comercial':
        # Solo puede rechazar solicitudes de Vendedor con precio en su rango
        if nivel_solicitante != 'Vendedor':
            raise HTTPException(
                status_code=403,
                detail="Gerencia Comercial solo puede rechazar solicitudes de Vendedores"
            )
        if precio_propuesto < precio_gerencia_com_min:
            raise HTTPException(
                status_code=403,
                detail="El precio propuesto está por debajo de su nivel de autorización. Debe ser procesado por Gerencia"
            )
    elif current_user["rol"] == 'Gerencia':
        # Puede rechazar solicitudes de Vendedor y Gerencia_Comercial
        if nivel_solicitante not in ['Vendedor', 'Gerencia_Comercial']:
            raise HTTPException(
                status_code=403,
                detail="No tiene autoridad para rechazar esta solicitud"
            )
    # admin puede rechazar cualquier solicitud (no hay restricción)
    
    # Rechazar solicitud
    cursor.execute("""
        UPDATE SolicitudesAutorizacion
        SET estado = 'Rechazada',
            autorizador_id = ?,
            fecha_respuesta = GETDATE(),
            comentarios_autorizador = ?
        WHERE id = ?
    """, (current_user["usuario_id"], respuesta.comentarios, solicitud_id))
    
    conn.commit()
    
    # Retornar solicitud actualizada
    cursor.execute("""
        SELECT id, sku, transporte, solicitante_id, solicitante, nivel_solicitante,
               precio_propuesto, precio_minimo_actual, descuento_adicional_pct,
               cliente, cantidad, justificacion, estado, autorizador_id, autorizador,
               fecha_solicitud, fecha_respuesta, comentarios_autorizador
        FROM vw_SolicitudesAutorizacion
        WHERE id = ?
    """, (solicitud_id,))
    
    row = cursor.fetchone()
    return schemas.SolicitudAutorizacion(
        id=row[0],
        sku=row[1],
        transporte=row[2],
        solicitante_id=row[3],
        solicitante=row[4],
        nivel_solicitante=row[5],
        precio_propuesto=row[6],
        precio_minimo_actual=row[7],
        descuento_adicional_pct=row[8],
        cliente=row[9],
        cantidad=row[10],
        justificacion=row[11],
        estado=row[12],
        autorizador_id=row[13],
        autorizador=row[14],
        fecha_solicitud=row[15],
        fecha_respuesta=row[16],
        comentarios_autorizador=row[17]
    )
